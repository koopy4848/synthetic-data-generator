from flask import Blueprint

test_blueprint = Blueprint('test', __name__)

from . import views  # noqa: E402

