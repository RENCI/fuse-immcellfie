FROM python:3.8-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app

RUN apk add gcc file make python3-dev musl-dev libffi-dev openssl-dev g++

RUN pip3 install --no-cache-dir -r /usr/src/app/requirements.txt

COPY api /usr/src/app/api
COPY tx-utils/src /usr/src/app
COPY data /usr/src/app/data

EXPOSE 8080

ENTRYPOINT ["gunicorn"]

CMD ["-w", "4", "-b", "0.0.0.0:8080", "--worker-class", "gevent", "api.server:create_app()"]