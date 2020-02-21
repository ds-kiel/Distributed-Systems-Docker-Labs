FROM python:3.6-alpine

RUN pip install bottle requests paste

COPY src /application/src
COPY frontend.py /application

WORKDIR /application

CMD ["python", "./frontend.py"]