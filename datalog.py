from bson import ObjectId

from mongo_setup import db

from flask import Blueprint, request, jsonify, make_response, Response
from datetime import datetime
import io
import csv
import zipfile

datalog = Blueprint('datalog', __name__)


class DataLog:
    def __init__(self, uploadedData, timePlayed, status, project, additional):
        self.uploadedData = uploadedData
        self.timePlayed = timePlayed
        self.status = status
        self.project = project
        self.additional = additional

    def save(self):
        collection = db['datalog']

        if not isinstance(self.project, ObjectId):
            self.project = ObjectId(self.project)

        data = {
            'uploadedData': self.uploadedData,
            'timePlayed': self.timePlayed,
            'status': self.status,
            'project': self.project,
            'additional': self.additional
        }

        result = collection.insert_one(data)
        return result.inserted_id

    def __str__(self):
        return f"{self.uploadedData} - {self.timePlayed} - {self.status} - {self.project}  - {self.additional}"


@datalog.route('/datalog/upload', methods=['POST'])
def create():
    data_hora_atual = datetime.now()

    data_hora_formatada = data_hora_atual.strftime("%Y-%m-%dT%H:%M:%SZ")

    time_played_str = request.form.get('timePlayed')

    time_played_datetime = datetime.strptime(time_played_str, "%Y-%m-%dT%H:%M:%SZ")

    uploadedData = datetime.strptime(data_hora_formatada, "%Y-%m-%dT%H:%M:%SZ")
    timePlayed = time_played_datetime
    status = request.form.get('status')
    project = request.form.get('project')
    additional = request.form.get('additional')

    log = DataLog(uploadedData, timePlayed, status, project, additional)
    log.save()

    return '', 200


@datalog.route('/datalog', methods=['GET'])
def get_all_data():
    project = request.args.get('project')
    query = {}
    collection = db['datalog']

    if project:
        query['project'] = project

    docs = list(collection.find(query))

    for log in docs:
        log['_id'] = str(log['_id'])
        log['timePlayed'] = log['timePlayed'].strftime("%Y-%m-%dT%H:%M:%SZ")
        log['uploadedData'] = log['uploadedData'].strftime("%Y-%m-%dT%H:%M:%SZ")

    return jsonify(docs)


@datalog.route('/datalog/latest-uploaded-total', methods=['GET'])
def get_latest_uploaded_data():
    project = request.args.get('project')
    query = {}
    collection = db['datalog']

    if project:
        query['project'] = project

    # Encontrar o registro mais recente ordenando por 'uploadedData' em ordem decrescente
    mais_recente = collection.find_one(query, sort=[('uploadedData', -1)])

    if mais_recente is None:
        return make_response(jsonify({"error": "Nenhum dado encontrado"}), 404)

    # Acessar o campo 'uploadedData' no documento mais recente
    data_mais_recente = mais_recente['uploadedData']

    return jsonify({"latestUploadedData": data_mais_recente.isoformat()})


@datalog.route('/datalog/status/count', methods=['GET'])
def perform_aggregation():
    collection = db['datalog']
    project = request.args.get('project')

    # Pipeline de agregação
    pipeline = []

    # Adicionar etapa de filtragem se 'project' estiver presente
    if project:
        pipeline.append({"$match": {"project": project}})

    pipeline.extend([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$project": {"status": "$_id", "_id": 0, "count": 1}}
    ])

    # Executar a operação de agregação
    aggregation_result = list(collection.aggregate(pipeline))

    return jsonify(aggregation_result)


def get_project_name_by_oid(project_oid):
    project = db['project'].find_one({'_id': ObjectId(project_oid)})
    if project:
        return project['name']
    else:
        return None


def get_oid_by_project_name(project_name):
    project = db['project'].find_one({'name': project_name})
    if project:
        return str(project['_id'])  # retorna o _id como uma string
    else:
        return None


# def get_all_documents(project=None):
#     datalog_collection = db['datalog']
#     query = {}
#
#     if project:
#         query['project'] = project
#
#     documents = list(datalog_collection.find(query))
#
#     for doc in documents:
#         project_oid = doc.get('project')
#         if project_oid:
#             project_name = get_project_name_by_oid(str(project_oid))
#             if project_name:
#                 doc['project'] = project_name
#
#     return documents


def get_all_documents(project=None):
    match_stage = {"$match": {}}  # Estágio inicial para combinar documentos

    if project:
        match_stage["$match"]["project"] = ObjectId(project)

    lookup_stage = {
        "$lookup": {
            "from": "project",  # Nome da coleção de projetos
            "localField": "project",
            "foreignField": "_id",
            "as": "project_info"
        }
    }

    project_stage = {
        "$project": {
            "_id": 1,
            "uploadedData": 1,
            "timePlayed": 1,
            "status": 1,
            "projectName": {"$arrayElemAt": ["$project_info.name", 0]},  # Acessa o primeiro elemento do array
            "additional": 1
        }
    }

    pipeline = [match_stage, lookup_stage, project_stage]

    result = list(db.datalog.aggregate(pipeline))
    print(result)

    return result


def generate_csv(documentos):
    output = io.StringIO()
    writer = csv.writer(output)

    if documentos:
        header = documentos[0].keys()
        writer.writerow(header)

    for doc in documentos:
        writer.writerow(doc.values())

    output.seek(0)
    return output


@datalog.route('/datalog/downloaddata', methods=['GET'])
def download_csv_zip():
    current_time = datetime.now()
    format_string = "%d%m%y_%H%M%S"
    formatted_time = current_time.strftime(format_string)
    filename_csv = "logs"

    project_name = request.args.get('project')
    project = get_oid_by_project_name(project_name)

    documents = get_all_documents(project)

    csv_data = generate_csv(documents)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(f"{filename_csv}_{formatted_time}.csv", csv_data.getvalue())

    # Configurar a resposta HTTP
    response = Response(zip_buffer.getvalue())
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = f"attachment; filename={filename_csv}_{formatted_time}.zip"

    return response


def serialize_document(doc):
    """ Converte ObjectId e outros tipos não serializáveis em strings. """
    if isinstance(doc, dict):
        return {key: serialize_document(value) for key, value in doc.items()}
    elif isinstance(doc, list):
        return [serialize_document(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)  # Converte ObjectId para string
    else:
        return doc  # Retorna o valor original se já for serializável


@datalog.route('/datalog/getdatabyproject', methods=['GET'])
def getdata():
    project_name = request.args.get('project')
    project = get_oid_by_project_name(project_name)

    documents = get_all_documents(project)

    # Convertendo os documentos para um formato JSON serializável
    serialized_documents = serialize_document(documents)

    return jsonify({
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "project": project_name,
        "data": serialized_documents
    })
