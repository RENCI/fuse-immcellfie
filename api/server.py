import connexion
from tx.connexion.utils import ReverseProxied


def create_app():
    app = connexion.FlaskApp(__name__, specification_dir="openapi/")
    app.add_api("my_api.yaml")
    flask_app = app.app
    proxied = ReverseProxied(flask_app.wsgi_app)
    flask_app.wsgi_app = proxied
    return app
