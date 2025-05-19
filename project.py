from datetime import datetime
import json

from mongo_setup import db
from flask import Blueprint, request, jsonify

project = Blueprint('project', __name__)


class Project:
    def __init__(self, name, createdAt, owner):
        self.name = name
        self.createdAt = createdAt
        self.owner = owner

    def save(self):
        collection = db['project']
        data = {
            'name': self.name,
            'createdAt': self.createdAt,
            'owner': self.owner
        }
        result = collection.insert_one(data)
        return result.inserted_id

    def __str__(self):
        return f"{self.name} - {self.createdAt} - {self.owner}"


@project.route('/project/upload', methods=['POST'])
def create():
    name = request.form.get('name')
    owner = request.form.get('owner')

    if not name or not owner:
        return jsonify({'error': 'Name and owner are required fields'}), 400

    data_hora_atual = datetime.now()
    data_hora_formatada = data_hora_atual.strftime("%Y-%m-%dT%H:%M:%SZ")
    createdAt = datetime.strptime(data_hora_formatada, "%Y-%m-%dT%H:%M:%SZ")

    prj = Project(name, createdAt, owner)
    prj.save()

    return '', 200

@project.route('/project')
def find_all():
    collection = db['project']

    docs = list(collection.find())

    for prj in docs:
        prj['_id'] = str(prj['_id'])
        prj['createdAt'] = prj['createdAt'].strftime("%Y-%m-%dT%H:%M:%SZ")

    return jsonify(docs)
