from flask_login import LoginManager, UserMixin, login_required, logout_user
from flask import render_template, redirect, url_for, request, Blueprint
from bson.objectid import ObjectId

from mongo_setup import db

# Initialize LoginManager and Blueprint
login_manager = LoginManager()
auth = Blueprint('auth', __name__)

users_collection = db['user_admin']


class UserAdmin(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        return None
    return UserAdmin(str(user_data['_id']))


@login_manager.unauthorized_handler
def unauthorized():
    return render_template('unauthorized.html')


@auth.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users_collection.find_one({"username": username}):
            return 'Nome de usuário já existe. Escolha outro nome de usuário.'
        users_collection.insert_one({"username": username, "password": password})
        return 'Cadastro realizado com sucesso. <a href="/">Ir para a página inicial</a>'
    return render_template('register.html')


@auth.route('/login', methods=['POST', 'GET'])
def login():
    # if request.method == 'POST':
    #     username = request.form['username']
    #     password = request.form['password']
    #     user_data = users_collection.find_one({"username": username})
    #     if user_data and user_data['password'] == password:
    #         user = UserAdmin(str(user_data['_id']))
    #         login_user(user)
    #         if request.form['submit_button'] == 'Entrar':
    #             return redirect(url_for('index'))
    #     return render_template('acesso_negado.html')
    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
