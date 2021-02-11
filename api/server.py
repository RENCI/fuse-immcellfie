import connexion
from flask_cors import CORS, cross_origin
from tx.connexion.utils import ReverseProxied


def create_app():
    app = connexion.FlaskApp(__name__, specification_dir="openapi/")
    cors = CORS(app)
    app.config["CORS_HEADERS"] = "Content-Type"
    app.add_api("my_api.yaml")
    flask_app = app.app
    proxied = ReverseProxied(flask_app.wsgi_app)
    flask_app.wsgi_app = proxied
    return app
