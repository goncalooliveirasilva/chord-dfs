'''app creation'''
from flask import Flask
from flask_smorest import Api
from app.api.files.routes import blp as FilesBlueprint
from app.api.system.routes import blp as SystemBlueprint

def create_app():
    '''flask app initialization'''
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Chord DFS API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    api = Api(app)

    api.register_blueprint(FilesBlueprint)
    app.register_blueprint(SystemBlueprint)

    return app
