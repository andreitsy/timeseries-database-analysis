import os
import rx
import sys
import psycopg2
import logging
import pandas as pd

from time import sleep
from pathlib import Path
from shutil import unpack_archive
from sqlalchemy import create_engine
from rx import operators as ops
from influxdb_client import InfluxDBClient, Point, WriteOptions
from pymongo import MongoClient

DIR_ARCHIVE = Path(os.environ["DUMP_DATA"])
FILES_DIR = "files"


def extract_tarfiles(dir_archive: Path):
    """Extract tar files with data"""
    logger = logging.getLogger('extract_tarfiles')
    archives = os.listdir(dir_archive)
    extract_path = dir_archive / FILES_DIR
    if not extract_path.exists():
        os.mkdir(extract_path)
    for filename in archives:
        try:
            if filename.endswith("tar.gz"):
                logger.info(
                    f"Unpacking {dir_archive / filename} to {extract_path}")
                unpack_archive(dir_archive / filename, extract_path)
        except Exception as e:
            logger.error("Error for unpacking", exc_info=e)
            continue


def connect_postgress():
    logger = logging.getLogger('connect_postgress')
    host = os.environ["POSTGRES_HOST"]
    db = os.environ["POSTGRES_DB"]
    user = os.environ["POSTGRES_USER"]
    passw = os.environ["POSTGRES_PASSWORD"]
    engine = create_engine(f'postgresql+psycopg2://{user}:{passw}@{host}/{db}',
                           pool_size=5, pool_recycle=3600)
    db_version = engine.execute('SELECT version();').fetchall()
    logger.info(db_version)
    return engine


def read_csv_dump(path_to_file: Path) -> pd.DataFrame:
    df = pd.read_csv(path_to_file, index_col=False)
    df.rename(columns={"Time": "TIME"}, inplace=True)
    df["OMDSEQ"] = df.index
    df.columns = map(str.lower, df.columns)
    return df


def load_data_to_postgress(files_dir: Path):
    files = os.listdir(files_dir)
    logger = logging.getLogger('load_data_to_postgress')
    logger.info(f"The following files will be loaded into postgress:\n{files}")
    sleep(2)
    engine = None
    try:
        engine = connect_postgress()
        for file in files:
            filepath = files_dir / file
            df = read_csv_dump(filepath)
            logger.info(f"Loading {filepath}...")
            if file.endswith("qte.csv"):
                with engine.begin() as connection:
                    df.to_sql('quotes', con=connection,
                              if_exists='append', index=False)
            elif file.endswith("trd.csv"):
                with engine.begin() as connection:
                    df.to_sql('trades', con=connection,
                              if_exists='append', index=False)
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error("Error with postgress", exc_info=error)


def parse_qte_influx_row(row):
    return (Point("quotes")
            .tag("symbol", row['symbol'])
            .field("bid_size", float(row['bid_size']))
            .field("ask_size", float(row['ask_size']))
            .field("bid_price", float(row['bid_price']))
            .field("ask_price", float(row['ask_price']))
            .field("omdseq", int(row['omdseq']))
            .time(row['time']))


def parse_trd_influx_row(row):
    return (Point("trades")
            .tag("symbol", row['symbol'])
            .field("size", float(row['size']))
            .field("price", float(row['price']))
            .field("omdseq", int(row['omdseq']))
            .time(row['time']))


def load_data_to_influx(files_dir: Path):
    files = os.listdir(files_dir)
    logger = logging.getLogger('load_data_to_influx')
    logger.info(f"The following files will be loaded into Influx DB:\n{files}")
    try:
        token = os.environ["INFLUXDB_V2_TOKEN"]
        org = os.environ["INFLUXDB_V2_ORG"]
        bucket = os.environ["INFLUX_BUCKET"]
        url_influx = os.environ["INFLUXDB_V2_URL"]
        logger.info(f"Client influx:\n token={token}\n org={org}"
                    f"\n bucket={bucket} \n url={url_influx}")
        with InfluxDBClient.from_env_properties(debug=True) as client:
            for file in files:
                filepath = files_dir / file
                df = read_csv_dump(filepath)
                logger.info(f"Loading {filepath}...")
                if file.endswith("qte.csv"):
                    parse_row = parse_qte_influx_row
                elif file.endswith("trd.csv"):
                    parse_row = parse_trd_influx_row
                with client.write_api(
                    write_options=WriteOptions(batch_size=5000,
                                               flush_interval=10_000,
                                               jitter_interval=2_000,
                                               retry_interval=5_000,
                                               max_retries=5,
                                               max_retry_delay=30_000)) as write_client:
                    data = (rx
                            .from_iterable(r for _, r in df.iterrows())
                            .pipe(ops.map(lambda row: parse_row(row))))
                    write_client.write(bucket=bucket, record=data)
    except Exception as error:
        logger.error("Error with influx", exc_info=error)


def load_data_to_mongo(files_dir: Path):
    files = os.listdir(files_dir)
    logger = logging.getLogger('load_data_to_mongo')
    logger.info(f"The following files will be loaded into MongoDB:\n{files}")
    try:
        client = MongoClient(
            f'mongodb://{os.environ["MONGODB_HOST"]}:{os.environ["MONGODB_PORT"]}/')
        db = client["quotes_trades"]
        for file in files:
            filepath = files_dir / file
            df = read_csv_dump(filepath)
            logger.info(f"Loading {filepath}...")
            if file.endswith("qte.csv"):
                collection = db["quotes"]
            elif file.endswith("trd.csv"):
                collection = db["trades"]
            records = df.to_dict('records')
            collection.insert_many(records)
        client.close()
    except Exception as error:
        logger.error("Error with mongo", exc_info=error)

def logging_setup():
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG)


if __name__ == "__main__":
    logging_setup()
    logger = logging.getLogger('main')

    extract_tarfiles(DIR_ARCHIVE)
    load_data_to_postgress(DIR_ARCHIVE / FILES_DIR)
    load_data_to_influx(DIR_ARCHIVE / FILES_DIR)
    load_data_to_mongo(DIR_ARCHIVE / FILES_DIR)
