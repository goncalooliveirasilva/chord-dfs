'''app creation'''
from flask import Flask
from app.chord.node import Node
from app.api.files.routes import blp as files_blp
from app.api.system.routes import blp as system_blp

def create_app():
    '''Flask app initialization'''
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True

    app.node = Node(address=("localhost", 5000))

    app.register_blueprint(files_blp)
    app.register_blueprint(system_blp)

    return app
