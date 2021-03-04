import connexion
from flask_cors import CORS
import api
from flask import request
import sys

def create_app():

    app = connexion.FlaskApp(__name__, specification_dir='openapi/')

    app.add_api('my_api.yaml')

    @app.app.route("/v1/plugin/<name>/<path:path>", methods=["GET", "POST", "DELETE"])
    def plugin(name, path):
        if request.method == "GET":
            return api.get_plugin(name, path, request.headers, kwargs=request.args.to_dict())
        elif request.method == "POST":
            return api.post_plugin(name, path, request.headers, request.stream, kwargs=request.args.to_dict())
        elif request.method == "DELETE":
            return api.delete_plugin(name, path, request.headers, request.stream, kwargs=request.args.to_dict())
        else:
            raise RuntimeError("unsupported method " + request.method)
        
    CORS(app.app)
    
    return app
