FROM python:3.8-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN apk add \
  gcc \
  libffi-dev \
  musl-dev \
  openssl-dev \
  file \
  make \ 
  g++ 
# cargo \
# rust 

# RUN export CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN pip3 install 'cryptography<=3'
RUN pip3 install --no-cache-dir \
  connexion[swagger-ui] \
  docker==4.3.0 \
  flask-cors \
  get_docker_secret==1.0.1 \
  gevent==20.9.0 \
  gunicorn[gevent]==20.0.4 \
  pymongo==3.11.0 \
  python-dateutil \
  python-jose[cryptography]

COPY api /usr/src/app/api
COPY tx /usr/src/app/tx
COPY tx-utils/src /usr/src/app
COPY sc.py /usr/src/app/sc.py

EXPOSE 8080

ENTRYPOINT ["gunicorn"]

CMD ["-w", "4", "-b", "0.0.0.0:8080", "-k", "gevent", "-c", "sc.py", "--timeout", "100000", "api.server:create_app()"]
