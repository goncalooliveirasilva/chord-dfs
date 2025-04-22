'''files blueprint'''
from flask.views import MethodView
from flask_smorest import Blueprint


blp = Blueprint("Files", __name__, description="Operations on files.")


@blp.route("/files/<filename>")
class FilesSpecific(MethodView):
    '''Operation with a specific file'''

    def post(self, filename):
        '''Uploads a file'''
        return {"message": f"File {filename} uploaded"}, 201

    def get(self, filename):
        '''Get a file'''
        return {"message": f"Returning file {filename}"}, 200

    def delete(self, filename):
        '''Delete a file'''
        return {"message": f"File {filename} deleted"}, 204



@blp.route("/files")
class FilesAll(MethodView):
    '''Operations with all files'''

    def get(self):
        '''List all files'''
        return {"message": "All files downloaded"}, 200

    def delete(self):
        '''Delete all files'''
        return {"message": "All files deleted"}, 204
