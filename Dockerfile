# syntax=docker/dockerfile:1
FROM python:latest
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY load_data_dbs.py /code/
EXPOSE 5432
