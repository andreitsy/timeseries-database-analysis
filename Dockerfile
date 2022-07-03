# syntax=docker/dockerfile:1
FROM python:3.9.13
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
EXPOSE 5432