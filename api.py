from flask import Flask, request, render_template
#import db

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register_lease():
    r = request.json
    db.register_lease(**r)
    return ""

@app.route('/')
@app.route('/<ip>')
def index(ip=None):
    return render_template('index.html', ip=ip)

if __name__ == '__main__':
    app.run(host= '0.0.0.0',port=8067,debug=True)
