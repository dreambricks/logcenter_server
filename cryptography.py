from flask import Blueprint, render_template

crypt = Blueprint('crypt', __name__)

@crypt.route('/crypt/generatekeys')
def generate_keys_page():
    return render_template('crypt/generate-keys.html')