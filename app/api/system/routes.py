'''system blueprint'''
import json
from flask.views import MethodView
from flask import Blueprint, request, current_app

blp = Blueprint("System", __name__, url_prefix="/chord")


class ChordSuccessor(MethodView):
    '''Successor operations on chord dht protocol'''

    def get(self):
        '''Get successor'''
        return {"message": "successor id here"}, 200


class ChordPredecessor(MethodView):
    '''Predecessor operations on chord dht protocol'''

    def get(self):
        '''Get predecessor'''


class ChordJoin(MethodView):
    '''Join operations on chord dht protocol'''

    def post(self):
        '''When a nodes is trying to join'''
        data = request.json
        joining_id = data["id"]
        joining_addr = tuple(data["address"].values())
        response = current_app.node.handle_join_request(joining_id, joining_addr)
        return json.dumps(response), 200


class ChordKeepAlive(MethodView):
    '''Operations on chord dht protocol'''

    def post(self):
        '''Keep-alive heartbeat'''
        return {"message": "keep-alive, ok?"}

blp.add_url_rule("/successor", view_func=ChordSuccessor.as_view("chord_successor"))
blp.add_url_rule("/keepalive", view_func=ChordKeepAlive.as_view("chord_keepalive"))
blp.add_url_rule("/predecessor", view_func=ChordPredecessor.as_view("chord_predecessor"))
blp.add_url_rule("/join", view_func=ChordJoin.as_view("chord_join"))
