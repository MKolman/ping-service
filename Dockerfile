FROM python:3.11-alpine

RUN apk add iputils

WORKDIR /app
COPY app/*.py /app/
COPY config/logging.prod.conf config/requirements.prod.txt /app/

RUN pip install -r requirements.prod.txt && mkdir log

ENV PROMETHEUS_DISABLE_CREATED_SERIES=True

EXPOSE 5000

ENTRYPOINT ["python3", "server.py", "--logging-config", "logging.prod.conf"]