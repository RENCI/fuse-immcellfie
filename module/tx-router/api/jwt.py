from werkzeug.exceptions import Unauthorized
from get_docker_secret import get_docker_secret

from jose import JWTError, jwt
import sys
import os
import time

JWT_ISSUER = 'pdsbackend'
JWT_SECRET = get_docker_secret("JWT_SECRET")
JWT_LIFETIME_SECONDS = 600
JWT_ALGORITHM = 'HS256'


def generate_token(user_id, scope):
    timestamp = time.time()
    payload = {
        "iss": JWT_ISSUER,
        "iat": timestamp,
        "exp": timestamp + JWT_LIFETIME_SECONDS,
        "sub": user_id,
        "scope": scope
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise Unauthorized from e


if __name__ == "__main__":
    cmd = sys.args[1]
    if cmd == "encode":
        user_id = sys.args[2]
        scope = sys.args[3:]
        print(generate_token(user_id, scope))
    else:
        print(decode_token(sys.args[2]))

