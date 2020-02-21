FROM python:alpine
WORKDIR /application

RUN pip install bottle requests dnspython

COPY ./*.py /application/

#CMD export HOST=${hostname -i} && python run.py