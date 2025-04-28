'''files blueprint'''
from io import BytesIO
from flask.views import MethodView
from flask import request, send_file, Blueprint, current_app


blp = Blueprint("Files", __name__, url_prefix="/files")


class FileResource(MethodView):
    '''Operation with a specific file'''

    def get(self, filename):
        '''Get a file'''
        status, file_path = current_app.node.get_file(filename)
        match status:
            case "local":
                # The node has the file
                return send_file(file_path, as_attachment=True, download_name=filename)
            case "forwarded":
                # The file arrives in bytes from other node
                return send_file(BytesIO(file_path), as_attachment=True, download_name=filename)
            case "not_found":
                return {"error": "File not found."}, 404

        return {"error": f"Error retrieving file: {file_path}"}, 500


    def delete(self, filename):
        '''Delete a file'''

        status, _ = current_app.node.delete_file(filename)
        match status:
            case "deleted":
                return {"message": f"File {filename} deleted successfully."}, 200
            case "not_found":
                return {"error": "File not found."}, 404

        return {"error": f"Error deleting file: {filename}"}, 500


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

        file_content = file.read()
        success = current_app.node.put_file(filename, file_content)

        if success:
            return {"message": f"File {filename} uploaded successfully via DHT."}, 201
        return {"error": "Failed to store file"}, 500

    def get(self):
        '''List all files'''
        # files = storage_service.list_files()
        # return {"files": files}, 200
        return {"message": "Not yet implemented."}, 204

    def delete(self):
        '''Delete all files'''
        # storage_service.delete_all_files()
        return {"message": "Not yet implemented."}, 204


class FileForwardResource(MethodView):
    '''Operations with files by the system'''

    def post(self):
        '''Forward file'''
        if "file" not in request.files:
            return {"error": "No file provided."}, 400

        file = request.files["file"]
        filename = file.filename
        file_content = file.read()

        success = current_app.node.put_file(filename, file_content)
        if success:
            return {"message": "File stored successfully."}, 201
        else:
            return {"error": "Failed to store file"}, 500




blp.add_url_rule("/<filename>", view_func=FileResource.as_view("file_resource"))
blp.add_url_rule("/", view_func=FileListResource.as_view("file_list"))
blp.add_url_rule("/forward", view_func=FileForwardResource.as_view("file_forward"))
