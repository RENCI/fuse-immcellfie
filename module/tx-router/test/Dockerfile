FROM python:3.8-alpine

RUN mkdir test
WORKDIR test

RUN pip3 install \
  connexion \
  docker==4.3.0 \
  get_docker_secret==1.0.1 \
  pymongo \
  pytest \
  pytest-timeout \
  python-dateutil \
  pyyaml \
  requests

RUN pip3 install requests-jwt
RUN pip3 install python-jose

COPY test/test_tx_router.py test_tx_router.py
COPY tx tx
COPY tx-utils/src .
COPY debug debug
COPY api api

ENTRYPOINT ["pytest"]



