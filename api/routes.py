import os

from flask import Response, request, jsonify


def hello_world():
    return "hello world"


def serve_file():
    if filename := request.args.get("filename"):
        try:
            content = get_file(filename)
            return Response(content, mimetype="text/html")
        except Exception:
            return jsonify(
                {
                    "These are the following files available": os.listdir(
                        "/usr/src/app/data"
                    )
                }
            )
    else:
        return "Please provide the filename query param ", 404


def root_dir():  # pragma: no cover
    return os.path.abspath(os.path.dirname(__file__))


def get_file(filename):  # pragma: no cover
    src = os.path.join("/usr/src/app/data/", filename)
    return open(src).read()
