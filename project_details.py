from flask import Blueprint

from mongo_setup import db

project_details = Blueprint('project_details', __name__)


@project_details.route('/project_details/login')
def find_all():
    return
