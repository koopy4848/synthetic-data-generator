from flask import Blueprint

# Create a Blueprint object
schema_blueprint = Blueprint('schema_sdg', __name__)


from . import schema_sdg_views  # This import is necessary to ensure the routes get registered
