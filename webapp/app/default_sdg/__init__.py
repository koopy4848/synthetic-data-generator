from flask import Blueprint

# Create a Blueprint object
default_blueprint = Blueprint('default_sdg', __name__)


from . import default_sdg_views  # This import is necessary to ensure the routes get registered
