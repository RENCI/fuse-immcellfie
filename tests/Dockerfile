FROM python:3.8-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY tests /usr/src/app/tests
COPY api /usr/src/app/api
COPY tx-utils/src /usr/src/app

RUN apk add gcc file make python3-dev musl-dev libffi-dev openssl-dev g++

RUN pip3 install --no-cache-dir -r /usr/src/app/test/requirements.txt

CMD ["python3", "-m", "pytest", "/usr/src/app/test/"]