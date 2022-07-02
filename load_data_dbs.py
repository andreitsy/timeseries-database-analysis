import os
import logging
import sys
from time import sleep
from shutil import unpack_archive
from pathlib import Path
import psycopg2
import pandas as pd
from sqlalchemy import create_engine

DIR_ARCHIVE = Path("/code/data")
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
    logger = logging.getLogger('load_data_to_postgress')
    files = os.listdir(files_dir)
    logger.info(f"The following files will be loaded:\n{files}")
    sleep(2)
    engine = None
    try:
        engine = connect_postgress()
        for file in files:
            filepath = files_dir / file
            df = read_csv_dump(filepath)
            logger.info(f"Loading {file}...")
            if file.endswith("qte.csv"):
                with engine.begin() as connection:
                    df.to_sql('quotes', con=connection, 
                              if_exists='append', index=False)
            elif file.endswith("trd.csv"):
                with engine.begin() as connection:
                    df.to_sql('trades', con=connection, 
                              if_exists='append', index=False)
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error("Error with cur run", exc_info=error)


def logging_setup():
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG)


if __name__ == "__main__":
    logging_setup()
    logger = logging.getLogger('main')

    extract_tarfiles(DIR_ARCHIVE)
    load_data_to_postgress(DIR_ARCHIVE / FILES_DIR)
