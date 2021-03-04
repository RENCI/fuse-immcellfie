FROM python:3.8-alpine

RUN pip3 install flask gunicorn==20.0.4

COPY echo.py echo.py

ENTRYPOINT ["gunicorn", "echo:app"]



