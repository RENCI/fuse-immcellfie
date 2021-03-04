from flask import Flask, jsonify, request, Response
from functools import wraps
from werkzeug.routing import Rule
from pprint import pprint
import time
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VERBOSE = 'verbose'
BASIC_AUTH = 'basic_auth'
AUTH_USERNAME = 'auth_username'
AUTH_PASSWORD = 'auth_password'

config = {
    BASIC_AUTH: False,
    VERBOSE: False
}

app = Flask(__name__)

app.url_map.add(Rule('/', defaults={'path' : ''}, endpoint='index'))
app.url_map.add(Rule('/<path:path>', endpoint='index'))


def validate_status_code(status_code):
    if status_code < 600:
        return True
    return False


def extract(d):
    return {key: value for (key, value) in d.items()}


def check_auth(username, password):
    if AUTH_USERNAME not in config or AUTH_PASSWORD not in config:
        return False

    return username == config[AUTH_USERNAME] and password == config[AUTH_PASSWORD]


def authenticate():
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not config[BASIC_AUTH]:
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.endpoint('index')
@requires_auth
def echo(path):

    status_code = request.args.get('status') or 200
    status_code = int(status_code)
    if not validate_status_code(status_code):
        status_code = 200

    data = {
        'success' : True,
        'status' : status_code,
        'time' : time.time(),
        'path' : request.path,
        'script_root' : request.script_root,
        'url' : request.url,
        'base_url' : request.base_url,
        'url_root' : request.url_root,
        'method' : request.method,
        'headers' : extract(request.headers),
        'data' : request.data.decode(encoding='UTF-8'),
        'host' : request.host,
        'args' : extract(request.args),
        'form' : extract(request.form),
        'json' : request.json,
        'cookies' : extract(request.cookies)
    }

    if config[VERBOSE]:
        pprint(data)

    response = jsonify(data)
    response.status_code = status_code
    return response


def main():
    host = os.environ["HOST"]
    port = os.environ["PORT"]
    auth = os.environ.get("AUTH")
    verbose = os.environ.get("VERBOSE") is not None
    debug = os.environ.get("DEBUG") is not None

    config[VERBOSE] = verbose

    if auth:
        username, password = auth.split(':')
        if username is None or password is None:
            logger.error('Invalid auth credentials {0}'.format(auth))

        config[BASIC_AUTH] = True
        config[AUTH_USERNAME] = username
        config[AUTH_PASSWORD] = password

    app.debug = debug
    app.run(port=int(port), host=host)


if __name__ == '__main__':
    main()
