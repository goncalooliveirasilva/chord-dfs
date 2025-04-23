'''system blueprint'''
from flask.views import MethodView
from flask import Blueprint

blp = Blueprint("System", __name__, url_prefix="/chord")


@blp.route("/successor")
class SystemSuccessor(MethodView):
    '''Operations on chord dht protocol'''

    def get(self):
        '''Get successor'''
        return {"message": "successor id here"}, 200


@blp.route("/keepalive")
class SystemKeepAlive(MethodView):
    '''Operations on chord dht protocol'''

    def post(self):
        '''Keep-alive heartbeat'''
        return {"message": "keep-alive, ok?"}
