import datetime
from flask import Flask, request, render_template
from urllib import parse
import db
import librenms
from mac import *

app = Flask(__name__)
DEFAULT_LIMIT = 20

# Test DB connection early
db.get_ip_history("0.0.0.0", 1)

macdb = MACdb()

@app.template_filter()
def format_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).isoformat(' ')


@app.template_filter()
def url_encode(s):
    return parse.quote_plus(s)

@app.template_filter()
def mac_search(mac):
    try:
        return macdb.search(mac)
    except MACNotFound:
        return 'UNKNOWN'
    except MACInvalid:
        return 'LOOKUP ERROR'

@app.template_filter()
def loc2addr(loc):
    return loc.split(',', 1)[0]

@app.route('/register', methods=['post'])
def register():
    events = request.json
    for event in events:
        print(event)
        if 'sw' in event.keys():
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
        history = db.get_ip_history(ip, limit=DEFAULT_LIMIT)
    else:
        history = None
    return render_template('index.html', ip=ip, history=history, limit=DEFAULT_LIMIT)


@app.route('/switches')
def switches():
    switches = librenms.get_switches()
    return render_template('switches.html', switches=switches)


@app.route('/switches/<hostname>')
def ports(hostname):
    location = librenms.get_location(hostname)
    ports = librenms.get_ports(hostname)
    return render_template('ports.html', hostname=hostname, location=location, ports=ports)


@app.route('/switches/<hostname>/<path:port>')
def port_details(hostname, port):
    location = librenms.get_location(hostname)
    ifalias = librenms.get_ifalias(hostname, port)
    history = db.get_port_history(hostname, port)
    return render_template('port_details.html', hostname=hostname, port=port, location=location, ifalias=ifalias, history=history)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8067, debug=True)
