FROM python:3.8-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN apk add gcc file make python3-dev musl-dev libffi-dev openssl-dev

RUN pip3 install --no-cache-dir flask gevent==20.9.0 gunicorn==20.0.4 connexion[swagger-ui] requests tx-functional python-dateutil

COPY api /usr/src/app/api
COPY tx-utils/src /usr/src/app

EXPOSE 8080

ENTRYPOINT ["gunicorn"]

CMD ["-w", "4", "-b", "0.0.0.0:8080", "--worker-class", "gevent", "api.server:create_app()"]