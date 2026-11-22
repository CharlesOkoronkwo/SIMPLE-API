import io

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def make_account(client, **extra):
    body = {"name": "Main", "layout": "manual", "opening_balance": 1000}
    body.update(extra)
    return client.post("/api/accounts", json=body)


def test_time_endpoint_still_works(client):
    resp = client.get("/time")
    assert resp.status_code == 200
    assert "current_time" in resp.get_json()


def test_health(client):
    assert client.get("/api/health").get_json()["status"] == "ok"


def test_create_and_list_accounts(client):
    assert make_account(client).status_code == 201
    names = [a["name"] for a in client.get("/api/accounts").get_json()]
    assert names == ["Main"]


def test_duplicate_account_is_a_400(client):
    make_account(client)
    resp = make_account(client)
    assert resp.status_code == 400
    assert "already exists" in resp.get_json()["error"]


def test_unknown_account_is_a_404(client):
    assert client.get("/api/accounts/42").status_code == 404


def test_add_transaction_and_balance(client):
    make_account(client)
    resp = client.post(
        "/api/accounts/1/transactions",
        json={"posted_on": "2025-03-02", "description": "UBER TRIP", "amount": -400},
    )
    assert resp.status_code == 201
    assert resp.get_json()["category"] == "transport"
    bal = client.get("/api/accounts/1/balance?as_of=2025-03-31").get_json()
    assert bal["balance"] == 600.0


def test_bad_transaction_is_a_400(client):
    make_account(client)
    resp = client.post(
        "/api/accounts/1/transactions",
        json={"posted_on": "not-a-date", "description": "x", "amount": 1},
    )
    assert resp.status_code == 400


def test_list_transactions_has_total(client):
    make_account(client)
    for day in ("2025-03-01", "2025-03-02"):
        client.post("/api/accounts/1/transactions",
                    json={"posted_on": day, "description": "x", "amount": -1})
    data = client.get("/api/accounts/1/transactions?start=2025-03-02").get_json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_edit_and_delete_transaction(client):
    make_account(client)
    client.post("/api/accounts/1/transactions",
                json={"posted_on": "2025-03-01", "description": "x", "amount": -1})
    resp = client.patch("/api/transactions/1", json={"category": "gifts"})
    assert resp.get_json()["category"] == "gifts"
    assert client.delete("/api/transactions/1").status_code == 204
    assert client.delete("/api/transactions/1").status_code == 404


def test_upload_a_statement(client):
    make_account(client, name="Savings", layout="bank_b")
    text = "Posted,Narration,Amount,Ref\n2025-03-05,NIP TRANSFER TO ADA,(5000.00),FT1\n"
    resp = client.post(
        "/api/accounts/1/import",
        data={"file": (io.BytesIO(text.encode()), "march.csv")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    assert resp.get_json()["rows_added"] == 1
    history = client.get("/api/accounts/1/imports").get_json()
    assert history[0]["filename"] == "march.csv"


def test_upload_without_a_file_is_a_400(client):
    make_account(client)
    assert client.post("/api/accounts/1/import").status_code == 400


def test_summary_endpoint(client):
    make_account(client)
    client.post("/api/accounts/1/transactions",
                json={"posted_on": "2025-03-05", "description": "SALARY", "amount": 5000})
    data = client.get("/api/accounts/1/summary?month=2025-03").get_json()
    assert data["money_in"] == 5000.0
    assert data["closing_balance"] == 6000.0


def test_bad_month_is_a_400(client):
    make_account(client)
    assert client.get("/api/accounts/1/summary?month=March").status_code == 400


def test_export_endpoint(client):
    make_account(client)
    client.post("/api/accounts/1/transactions",
                json={"posted_on": "2025-03-05", "description": "SALARY", "amount": 5000})
    resp = client.get("/api/accounts/1/export.csv")
    assert resp.mimetype == "text/csv"
    assert "SALARY" in resp.get_data(as_text=True)


def test_budget_round_trip(client):
    make_account(client)
    client.put("/api/accounts/1/budgets", json={"category": "transport", "monthly_cap": 5000})
    rows = client.get("/api/accounts/1/budgets?month=2025-03").get_json()
    assert rows[0]["category"] == "transport"
