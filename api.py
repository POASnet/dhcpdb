import datetime
from flask import Flask, request, render_template
import db

app = Flask(__name__)
DEFAULT_LIMIT = 20

# Test DB connection early
db.get_history("0.0.0.0", 1)


@app.template_filter()
def format_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).isoformat(' ')


@app.route('/register', methods=['post'])
def register():
    events = request.json
    for event in events:
        if 'ip' in event.keys() and 'sw' in event.keys():
            db.register_compat(**event)
        elif 'sw' in event.keys():
            db.register_client(**event)
        elif 'ip' in event.keys():
            db.register_lease(**event)
        else:
            return "Bad event: " + str(event), 400

    return ""


@app.route('/')
@app.route('/<ip>')
def index(ip=None):
    if ip:
        history = db.get_history(ip, limit=DEFAULT_LIMIT)
    else:
        history = None
    return render_template('index.html', ip=ip, history=history, limit=DEFAULT_LIMIT)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8067, debug=True)
