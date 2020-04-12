FROM python:3.7-alpine

RUN mkdir -p /cronicle/cronicle

COPY requirements.txt /cronicle
RUN pip install --requirement /cronicle/requirements.txt

COPY cronicle /cronicle/cronicle
COPY *.py README.md /cronicle/

WORKDIR /cronicle
RUN python3 setup.py install

ENTRYPOINT ["cronicle"]
CMD ["--help"]
