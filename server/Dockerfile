FROM python:3.9-alpine
WORKDIR /application

RUN pip install bottle requests paste

COPY ./*.py /application/

CMD ["python", "-u", "./server.py"]