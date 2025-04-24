'''files blueprint'''
from flask.views import MethodView
from flask import request, send_file, Blueprint
from app.services import storage_service


blp = Blueprint("Files", __name__, url_prefix="/files")


class FileResource(MethodView):
    '''Operation with a specific file'''

    def get(self, filename):
        '''Get a file'''
        file_path = storage_service.get_file_path(filename)
        if file_path:
            return send_file(file_path, as_attachment=True)
        return {"error": "File not found."}, 404


    def delete(self, filename):
        '''Delete a file'''
        if storage_service.delete_file(filename):
            return {"message": f"File {filename} deleted successfully."}, 200
        return {"error": "File not found."}, 404


class FileListResource(MethodView):
    '''Operations with all files'''

    def post(self):
        '''Saves a file'''
        if "file" not in request.files:
            return {"error": "No file provided."}, 400

        file = request.files["file"]
        filename = file.filename
        if filename == "":
            return {"error": "No selected file"}, 400

        storage_service.save_file(file, filename)
        return {"message": f"File {filename} uploaded successfully."}, 201

    def get(self):
        '''List all files'''
        files = storage_service.list_files()
        return {"files": files}, 200

    def delete(self):
        '''Delete all files'''
        storage_service.delete_all_files()
        return {"message": "All files deleted"}, 204


blp.add_url_rule("/<filename>", view_func=FileResource.as_view("file_resource"))
blp.add_url_rule("/", view_func=FileListResource.as_view("file_list"))
