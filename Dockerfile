FROM python:3.7-alpine

WORKDIR /cronicle

COPY requirements.txt ./
RUN pip install --requirement requirements.txt

COPY ./cronicle ./cronicle
COPY *.py README.rst ./

RUN python3 setup.py install

ENTRYPOINT ["cronicle"]
CMD ["--help"]
