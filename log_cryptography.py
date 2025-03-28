from flask import Blueprint, render_template, request

crypt = Blueprint('crypt', __name__)

@crypt.route('/crypt/generatekeys')
def generate_keys_page():
    return render_template('crypt/generate-keys.html')

@crypt.route('/crypt/decrypt')
def decrypt():
    project = request.args.get('project')
    return render_template('crypt/decrypt.html', project=project)
