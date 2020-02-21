FROM python:3.6-alpine
WORKDIR /application

RUN pip install bottle requests

COPY ./*.py /application/

CMD ["python", "./server.py"]