from io import StringIO
from flask import Blueprint, render_template, request, jsonify, send_file, request_started, Response
from dbcrypt import db_decrypt_string
import requests

crypt = Blueprint('crypt', __name__)


@crypt.route('/crypt/generatekeys')
def generate_keys_page():
    return render_template('crypt/generate-keys.html')


@crypt.route('/crypt/decrypt')
def decrypt():
    project = request.args.get('project')
    return render_template('crypt/decrypt.html', project=project)


@crypt.route('/crypt/decrypt-data', methods=['POST'])
def decrypt_data():
    if 'decript_key' not in request.files or 'project' not in request.form:
        return jsonify({"error": "Chave privada e nome do projeto são obrigatórios."}), 400

    file = request.files['decript_key']
    private_key = file.read().decode('utf-8')
    project = request.form['project']

    try:
        data = get_encrypted_data_by_project(project)

        encrypted_lines = [
            item['additional'] for item in data if item.get('additional')
        ]

        decrypted_lines = []
        for line in encrypted_lines:
            line = line.strip()
            if not line:
                continue
            try:
                decrypted = db_decrypt_string(line, private_key)
                decrypted_lines.append(decrypted)
            except Exception as e:
                print(f"Erro ao descriptografar linha: {line} - {e}")
                # Linha será ignorada
                continue

        output = StringIO()
        for row in decrypted_lines:
            output.write(row + '\n')

        csv_string = output.getvalue()
        output.close()

        filtered_lines = [line for line in csv_string.splitlines() if line.strip()]
        final_csv = '\n'.join(filtered_lines)

        return Response(final_csv, mimetype='text/csv')

    except Exception as e:
        return jsonify({
            "error": "Erro durante o processo de descriptografia.",
            "details": str(e)
        }), 500


def get_encrypted_data_by_project(project_name: str):
    try:
        base_url = request.host_url.rstrip('/')
        response = requests.get(f'{base_url}/datalog/getdatabyproject', params={'project': project_name})
        response.raise_for_status()
        json_data = response.json()

        if isinstance(json_data.get('data'), list):
            return json_data['data']
        elif isinstance(json_data.get('data'), dict) and 'additional' in json_data['data']:
            return [json_data['data']]
        else:
            return []

    except requests.RequestException as e:
        print(f"Erro ao buscar dados criptografados: {e}")
        return []
