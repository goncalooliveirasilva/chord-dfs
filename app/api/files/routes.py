'''files blueprint'''
from flask.views import MethodView
from flask_smorest import Blueprint


blp = Blueprint("Files", __name__, description="Operations on files.")


@blp.route("/upload/<filename>")
class FilesUpload(MethodView):
    '''Upload a file'''
    def post(self):
        '''Save a file'''


@blp.route("/files/<filename>")
class FilesSpecific(MethodView):
    '''Operation with a specific file'''
    def get(self):
        '''Get a file'''

    def delete(self):
        '''Delete a file'''



@blp.route("/files")
class FilesAll(MethodView):
    '''Operations with all files'''
    def get(self):
        '''List all files'''


    def delete(self):
        '''Delete all files'''
