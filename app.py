from flask import Flask
from datetime import datetime
import pytz

from ledger.api import bp as ledger_bp

app = Flask(__name__)
app.register_blueprint(ledger_bp)


@app.route('/time', methods=['GET'])
def get_time():
    wat = pytz.timezone('Africa/Lagos')
    return {'current_time': datetime.now(wat).strftime('%Y-%m-%d %H:%M:%S')}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
