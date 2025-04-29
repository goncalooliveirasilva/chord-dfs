'''system blueprint'''
from flask.views import MethodView
from flask import Blueprint, request, current_app


blp = Blueprint("System", __name__, url_prefix="/chord")


class ChordSuccessor(MethodView):
    '''Successor operations on chord dht protocol'''

    def post(self):
        '''Find successor'''
        data = request.json
        lookup_id = data["id"]
        requester = tuple(data["requester"])
        response = current_app.node.find_successor(lookup_id, requester)
        return response, 200


class ChordPredecessor(MethodView):
    '''Predecessor operations on chord dht protocol'''

    def get(self):
        '''Get predecessor of a node'''
        predecessor_info = current_app.node.get_predecessor()
        return predecessor_info, 200


class ChordNotify(MethodView):
    '''Predecessor operations on chord dht protocol'''

    def post(self):
        '''Update predecessor pointers endpoint'''
        data = request.json
        predecessor_id = data["predecessor_id"]
        predecessor_addr = tuple(data["predecessor_addr"])
        response = current_app.node.handle_notify(predecessor_id, predecessor_addr)
        return response, 200


class ChordJoin(MethodView):
    '''Join operations on chord dht protocol'''

    def post(self):
        '''When a nodes is trying to join'''
        data = request.json
        joining_id = data["id"]
        joining_addr = tuple(data["address"])
        response = current_app.node.handle_join_request(joining_id, joining_addr)
        return response, 200


class ChordInfo(MethodView):
    '''Info operations on chord dht protocol'''

    def get(self):
        '''Get info from a node'''
        node = current_app.node
        return {
            "id": node.id,
            "address": node.address,
            "successor_id": node.successor_id,
            "successor_addr": node.successor_address,
            "predecessor_id": node.predecessor_id,
            "predecessor_addr": node.predecessor_address,
            "finger_table": str(node.finger_table),
            "files": node.list_all_files()
        }


class ChordKeepAlive(MethodView):
    '''Operations on chord dht protocol'''

    def post(self):
        '''Keep-alive heartbeat'''
        return {"message": "Are you alive?"}


blp.add_url_rule("/successor", view_func=ChordSuccessor.as_view("chord_successor"))
blp.add_url_rule("/predecessor", view_func=ChordPredecessor.as_view("chord_predecessor"))
blp.add_url_rule("/notify", view_func=ChordNotify.as_view("chord_notify"))
blp.add_url_rule("/join", view_func=ChordJoin.as_view("chord_join"))
blp.add_url_rule("/info", view_func=ChordInfo.as_view("chord_info"))
blp.add_url_rule("/keepalive", view_func=ChordKeepAlive.as_view("chord_keepalive"))
