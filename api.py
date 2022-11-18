import datetime
from flask import Flask, request, render_template
import db

app = Flask(__name__)
DEFAULT_LIMIT = 20

@app.template_filter()
def format_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).isoformat(' ')

@app.route('/register', methods=['POST'])
def register_leases():
    ls = request.json
    for l in ls:
        db.register_lease(**l)
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
    app.run(host= '0.0.0.0',port=8067,debug=True)
