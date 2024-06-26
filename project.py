from datetime import datetime
import json

from mongo_setup import db
from flask import Blueprint, request, jsonify

project = Blueprint('project', __name__)


class Project:
    def __init__(self, _id, name, createdAt):
        self._id = _id
        self.name = name
        self.createdAt = createdAt

    def save(self):
        collection = db['project']
        data = {
            'name': self.name,
            'createdAt': self.createdAt
        }
        result = collection.insert_one(data)
        return result.inserted_id

    def __str__(self):
        return f"{self.name} - {self.createdAt}"


@project.route('/project/upload', methods=['POST'])
def create():
    data_hora_atual = datetime.now()

    data_hora_formatada = data_hora_atual.strftime("%Y-%m-%dT%H:%M:%SZ")

    createdAt = datetime.strptime(data_hora_formatada, "%Y-%m-%dT%H:%M:%SZ")

    name = request.form.get('name')

    prj = Project(name, createdAt)
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
