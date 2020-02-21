FROM python:alpine

WORKDIR /application

RUN pip install toxiproxy-python
RUN pip install bottle requests

COPY ./*.py /application/


ENV NUM_SERVERS 0

CMD [ "python", "./proxy.py" ]