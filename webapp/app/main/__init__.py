from flask import Blueprint

# Create a Blueprint object
main = Blueprint('main', __name__)

# Import the views module to associate the routes with the blueprint
from . import views
