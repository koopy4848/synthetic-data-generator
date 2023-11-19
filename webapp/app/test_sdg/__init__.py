from flask import Blueprint

test_blueprint = Blueprint('test', __name__)

from . import views  # This import is necessary to ensure the routes get registered

