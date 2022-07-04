import os
import sys
import logging
from timeit import default_timer as timer
from influxdb_client import InfluxDBClient, Point, WriteOptions
from pymongo import MongoClient
from sqlalchemy import create_engine

def get_postgres_client():
    logger = logging.getLogger('connect_postgress')
    host = os.environ["POSTGRES_HOST"]
    db = os.environ["POSTGRES_DB"]
    user = os.environ["POSTGRES_USER"]
    passw = os.environ["POSTGRES_PASSWORD"]
    engine = create_engine(f'postgresql+psycopg2://{user}:{passw}@{host}/{db}',
                           pool_size=10, pool_recycle=3600)
    return engine

def get_mongo_client():
    try:
        client = MongoClient(
            f'mongodb://{os.environ["MONGODB_HOST"]}:{os.environ["MONGODB_PORT"]}/')
        return client
    except Exception as error:
        logger.error("Error with mongo", exc_info=error)

def logging_setup():
    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG)

def measure_time_postgresql():
    logger = logging.getLogger('Postgres DB time measure')
    client = get_postgres_client()
    query_average = """
        SELECT 
            symbol, AVG(price) AS average_price
        FROM 
            trades
        GROUP BY
	        symbol"""
    average_t_price = count_avg_time(
        lambda _ : engine.execute(query_average).fetchall())
    logger.info(f"price average query: {average_t_price}")
    query_mid_price = """
        SELECT 
            symbol, AVG((ask_price + bid_price)/2) AS mid_price
        FROM 
            quotes
        GROUP BY
            symbol"""
    average_t_mid_price = count_avg_time(
        lambda _ : engine.execute(query_mid_price).fetchall())
    logger.info(f"price average query: {average_t_mid_price}")
    client.close()

def measure_time_mongo():
    logger = logging.getLogger('Mongo DB time measure')
    client = get_mongo_client()

def count_avg_time(func):
    avg_time = 0
    num = 5
    for x in range(num):
        start = timer()
        func()
        end = timer()
        avg_time += end - start
    return avg_time / num

if __name__ == "__main__":
    logging_setup()
    measure_time_postgresql()
    