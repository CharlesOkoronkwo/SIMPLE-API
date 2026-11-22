import os
import tempfile

from flask import Blueprint, Response, g, jsonify, request

from . import (accounts, budgets, categories, db, export, summary,
               transactions)
from .dates import month_bounds, today_iso
from .importer import import_file, import_history

bp = Blueprint("ledger", __name__, url_prefix="/api")


def get_conn():
    if "conn" not in g:
        g.conn = db.connect()
    return g.conn


@bp.teardown_app_request
def close_conn(error=None):
    conn = g.pop("conn", None)
    if conn is not None:
        conn.close()


@bp.errorhandler(ValueError)
def bad_request(err):
    return jsonify({"error": str(err)}), 400


@bp.errorhandler(LookupError)
def not_found(err):
    return jsonify({"error": str(err)}), 404


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("send a JSON object")
    return data


@bp.route("/health")
def health():
    return jsonify({"status": "ok", "accounts": len(accounts.list_accounts(get_conn()))})


# accounts

@bp.route("/accounts", methods=["GET"])
def list_accounts():
    return jsonify([a.to_dict() for a in accounts.list_accounts(get_conn())])


@bp.route("/accounts", methods=["POST"])
def create_account():
    data = body()
    account = accounts.create_account(
        get_conn(),
        data.get("name"),
        data.get("layout", "manual"),
        data.get("opening_balance", 0),
    )
    return jsonify(account.to_dict()), 201


@bp.route("/accounts/<int:account_id>", methods=["GET"])
def show_account(account_id):
    return jsonify(accounts.get_account(get_conn(), account_id).to_dict())


@bp.route("/accounts/<int:account_id>", methods=["PATCH"])
def update_account(account_id):
    data = body()
    conn = get_conn()
    if "name" in data:
        accounts.rename_account(conn, account_id, data["name"])
    if "opening_balance" in data:
        accounts.set_opening_balance(conn, account_id, data["opening_balance"])
    return jsonify(accounts.get_account(conn, account_id).to_dict())


@bp.route("/accounts/<int:account_id>", methods=["DELETE"])
def remove_account(account_id):
    accounts.delete_account(get_conn(), account_id)
    return "", 204


# balance and transactions

@bp.route("/accounts/<int:account_id>/balance")
def balance(account_id):
    as_of = request.args.get("as_of") or today_iso()
    value = transactions.balance_as_of(get_conn(), account_id, as_of)
    return jsonify({"account_id": account_id, "as_of": as_of, "balance": value})


@bp.route("/accounts/<int:account_id>/transactions", methods=["GET"])
def list_transactions(account_id):
    conn = get_conn()
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = int(request.args.get("offset", 0))
    rows = transactions.list_transactions(
        conn,
        account_id,
        start=request.args.get("start"),
        end=request.args.get("end"),
        category=request.args.get("category"),
        text=request.args.get("q"),
        limit=limit,
        offset=offset,
    )
    total = transactions.count_transactions(
        conn, account_id, request.args.get("start"), request.args.get("end")
    )
    return jsonify({"total": total, "items": [t.to_dict() for t in rows]})


@bp.route("/accounts/<int:account_id>/transactions", methods=["POST"])
def add_transaction(account_id):
    data = body()
    tx = transactions.add_transaction(
        get_conn(),
        account_id,
        data.get("posted_on"),
        data.get("description"),
        data.get("amount"),
        reference=data.get("reference"),
        category=data.get("category"),
    )
    return jsonify(tx.to_dict()), 201


@bp.route("/transactions/<int:tx_id>", methods=["PATCH"])
def edit_transaction(tx_id):
    data = body()
    tx = transactions.update_transaction(
        get_conn(), tx_id, description=data.get("description"), category=data.get("category")
    )
    return jsonify(tx.to_dict())


@bp.route("/transactions/<int:tx_id>", methods=["DELETE"])
def remove_transaction(tx_id):
    transactions.delete_transaction(get_conn(), tx_id)
    return "", 204


# imports

@bp.route("/accounts/<int:account_id>/import", methods=["POST"])
def upload_statement(account_id):
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        raise ValueError("attach a CSV file in the 'file' field")
    suffix = os.path.splitext(upload.filename)[1] or ".csv"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        upload.save(tmp)
        temp_path = tmp.name
    try:
        # keep the name the user uploaded so the history reads well
        named = os.path.join(os.path.dirname(temp_path), os.path.basename(upload.filename))
        os.replace(temp_path, named)
        temp_path = named
        result = import_file(get_conn(), account_id, temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return jsonify(result.to_dict()), 201


@bp.route("/accounts/<int:account_id>/imports")
def imports(account_id):
    accounts.get_account(get_conn(), account_id)
    return jsonify(import_history(get_conn(), account_id))


# reports

@bp.route("/accounts/<int:account_id>/summary")
def month_summary(account_id):
    month = request.args.get("month") or today_iso()[:7]
    return jsonify(summary.month_summary(get_conn(), account_id, month))


@bp.route("/accounts/<int:account_id>/series")
def series(account_id):
    month = request.args.get("month") or today_iso()[:7]
    count = max(1, min(int(request.args.get("months", 6)), 24))
    accounts.get_account(get_conn(), account_id)
    return jsonify(summary.monthly_series(get_conn(), account_id, month, count))


@bp.route("/accounts/<int:account_id>/compare")
def compare(account_id):
    month = request.args.get("month") or today_iso()[:7]
    accounts.get_account(get_conn(), account_id)
    return jsonify(summary.compare_with_previous(get_conn(), account_id, month))


@bp.route("/accounts/<int:account_id>/running-balance")
def running(account_id):
    month = request.args.get("month") or today_iso()[:7]
    start, end = month_bounds(month)
    return jsonify(transactions.running_balance(get_conn(), account_id, start, end))


@bp.route("/accounts/<int:account_id>/export.csv")
def export_account(account_id):
    import io

    buffer = io.StringIO()
    export.export_csv(
        get_conn(), account_id, buffer,
        start=request.args.get("start"), end=request.args.get("end"),
    )
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=account-%d.csv" % account_id},
    )


# budgets and rules

@bp.route("/accounts/<int:account_id>/budgets", methods=["GET"])
def show_budgets(account_id):
    month = request.args.get("month") or today_iso()[:7]
    accounts.get_account(get_conn(), account_id)
    return jsonify(budgets.budget_status(get_conn(), account_id, month))


@bp.route("/accounts/<int:account_id>/budgets", methods=["PUT"])
def put_budget(account_id):
    data = body()
    budgets.set_budget(get_conn(), account_id, data.get("category"), data.get("monthly_cap"))
    return jsonify(budgets.list_budgets(get_conn(), account_id))


@bp.route("/rules", methods=["GET"])
def show_rules():
    return jsonify(categories.list_rules(get_conn()))


@bp.route("/rules", methods=["POST"])
def post_rule():
    data = body()
    categories.add_rule(get_conn(), data.get("keyword"), data.get("category"))
    return jsonify(categories.list_rules(get_conn())[:20]), 201
