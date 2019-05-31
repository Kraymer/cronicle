FROM python:3.7-alpine

COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt

COPY cronicle /

WORKDIR /cronicle
