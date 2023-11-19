from flask import Flask
from .default_sdg import default_blueprint
from .test_sdg import test_blueprint


def create_app():
    app = Flask(__name__)
    app.register_blueprint(test_blueprint)
    app.register_blueprint(default_blueprint)
    return app
