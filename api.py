from flask import Flask, request
import db

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register_lease():
    r = request.json
    db.register_lease(**r)
    return ""

if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True)
