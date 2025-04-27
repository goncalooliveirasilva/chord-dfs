'''app creation'''
import os
import logging
from flask import Flask
from app.chord.node import Node
from app.api.files.routes import blp as files_blp
from app.api.system.routes import blp as system_blp

def create_app():
    '''Flask app initialization'''
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True

    log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    log_file = "chord_node.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)

    # host = os.environ.get("HOST", "localhost")
    port = int(os.environ.get("PORT", 5000))

    chord_host = os.environ.get("CHORD_HOST")

    some_node_host = os.environ.get("SOME_NODE_HOST")
    some_node_port = os.environ.get("SOME_NODE_PORT")

    some_node_address = None
    if some_node_host and some_node_port:
        some_node_address = (some_node_host, int(some_node_port))

    app.node = Node(address=(chord_host, port), some_node_address=some_node_address)

    app.register_blueprint(files_blp)
    app.register_blueprint(system_blp)

    return app
