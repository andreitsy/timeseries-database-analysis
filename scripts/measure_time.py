import os
import sys
import logging
from functools import partial
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


def get_influx_client():
    token = os.environ["INFLUXDB_V2_TOKEN"]
    org = os.environ["INFLUXDB_V2_ORG"]
    bucket = os.environ["INFLUX_BUCKET"]
    url_influx = os.environ["INFLUXDB_V2_URL"]
    return InfluxDBClient.from_env_properties(debug=False)


def logging_setup():
    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG)


def measure_time_postgresql():
    logger = logging.getLogger('Postgres DB')
    engine = get_postgres_client()
    logger.info("Postgres DB time measure")

    def f(query):
        return engine.execute(query).fetchall()

    query_average = """
        SELECT 
            symbol, AVG(price) AS average_price
        FROM 
            trades
        GROUP BY
	        symbol"""
    average_t_price = count_avg_time(partial(f, query_average))
    logger.info(f"Average time query_average: {average_t_price}")
    query_mid_price = """
        SELECT 
            symbol, AVG((ask_price + bid_price)/2) AS mid_price
        FROM 
            quotes
        GROUP BY
            symbol"""
    average_t_mid_price = count_avg_time(partial(f, query_mid_price))
    logger.info(f"Average time query_mid_price: {average_t_mid_price}")
    logger.info("closing connection...\n")


def measure_time_mongo():
    logger = logging.getLogger('Mongo DB')
    client = get_mongo_client()
    db = client["quotes_trades"]
    logger.info("Mongo DB time measure")

    query_average = [
        {
            '$group': {
                '_id': "$symbol",
                'avg': {'$avg': "$price"}
            }
        }
    ]
    average_t_price = count_avg_time(
        lambda *args: db.trades.aggregate(query_average))
    logger.info(f"Average time query_average: {average_t_price}")

    query_mid_price = [
        {
            "$addFields": {
                "sum_price": {"$add": ['$ask_price', '$bid_price']}
            }
        },
        {
            "$addFields": {
                "mid_price": {"$multiply": ["$sum_price", 0.5]}
            }
        },
        {
            "$group": {
                "_id": "$symbol",
                "avg": {"$avg": "$mid_price"}
            }
        }
    ]
    average_t_mid_price = count_avg_time(
        lambda *args: db.quotes.aggregate(query_mid_price))
    logger.info(f"Average time query_mid_price: {average_t_mid_price}")
    logger.info("closing connection...\n")
    client.close()


def measure_time_influx():
    logger = logging.getLogger('Influx DB')
    logger.info("Influx DB time measure")
    client = get_influx_client()
    query_api = client.query_api()
    query_average = """
    from(bucket:"quotes_trades")
        |> range(start: 0, stop: now())
        |> filter(fn: (r) => r._measurement == "trades" and r._field == "price")
        |> mean()
        |> yield()
    """
    average_t_price = count_avg_time(
        lambda *args: query_api.query(query_average))
    logger.info(f"Average time query_average: {average_t_price}")

    query_mid_price = """
    ask_stream = from(bucket:"quotes_trades")
        |> range(start: 0, stop: now())
        |> filter(fn: (r) => r._measurement == "quotes" and r._field == "ask_price")
        |> mean()

    bid_stream = from(bucket:"quotes_trades")
        |> range(start: 0, stop: now())
        |> filter(fn: (r) => r._measurement == "quotes" and r._field == "bid_price")
        |> mean()

    join(tables: {ask: ask_stream, bid: bid_stream}, on: ["symbol"])
        |> map(fn: (r) => ({symbol: r.symbol, _time: r._time, 
                            mid_price: (r._value_ask + r._value_bid) / 2.0}))
        |> yield()
    """
    average_t_mid_price = count_avg_time(lambda *args: query_api.query(query_mid_price))
    logger.info(f"Average time query_mid_price: {average_t_mid_price}")
    logger.info("closing connection...\n")
    client.close()


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
    measure_time_mongo()
    measure_time_influx()
