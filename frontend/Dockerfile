FROM python:alpine

RUN pip install bottle requests

COPY src /application/src
COPY frontend.py /application

WORKDIR /application

CMD ["python", "./frontend.py", "$NUM_SERVERS", "$FROM_PORT", "$TO_PORT"]