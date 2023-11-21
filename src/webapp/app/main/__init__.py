from flask import Blueprint

# Create a Blueprint object
main = Blueprint('main', __name__)


from . import views  # noqa: E402
