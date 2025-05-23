import os
from flask import Flask, render_template, request
from flask_cors import CORS
from log_cryptography import crypt
from datalog import datalog
from login_manager import auth
from project import project
from project_details import project_details
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
load_dotenv()
app.config.from_pyfile('config.py')

app.register_blueprint(datalog)
app.register_blueprint(project)
app.register_blueprint(project_details)
app.register_blueprint(auth)
app.register_blueprint(crypt)


# Rotas
@app.route('/')
def home():
    return render_template('login.html')


@app.route('/alive', methods=['GET'])
def alive():
    return "alive"


def get_client_ip():
    if 'X-Forwarded-For' in request.headers:
        user_ip = request.headers['X-Forwarded-For']
    else:
        user_ip = request.remote_addr
    return user_ip


if __name__ == '__main__':
    if os.getenv("LOCAL_SERVER"):
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        context = ('priv/fullchain.pem', 'priv/privkey.pem')
        app.run(host='0.0.0.0', port=5000, ssl_context=context)
