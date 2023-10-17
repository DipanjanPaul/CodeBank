# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip install  -r requirements.txt 

EXPOSE 4000

COPY . .
CMD [ "python", "bid_response_pivot_table.py", "4000", "--host=0.0.0.0"]

