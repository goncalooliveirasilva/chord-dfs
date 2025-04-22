'''system blueprint'''
from flask.views import MethodView
from flask_smorest import Blueprint

blp = Blueprint("System", __name__, url_prefix="/chord", description="Internal System ooperations.")


@blp.route("/successor")
class SystemSuccessor(MethodView):
    '''Operations on chord dht protocol'''
    def get(self):
        '''Get successor'''


@blp.route("/keepalive")
class SystemKeepAlive(MethodView):
    '''Operations on chord dht protocol'''
    def post(self):
        '''Keep-alive heartbeat'''
