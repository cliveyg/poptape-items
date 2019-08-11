# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config(object):
    # set app configs
    SECRET_KEY = os.getenv('SECRET_KEY')
    CHECK_ACCESS_URL = os.getenv('CHECK_ACCESS_URL')
    LOG_FILENAME = os.getenv('LOG_FILENAME')
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    FERNET_KEY = os.getenv('FERNET_KEY')
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
    PAGE_LIMIT = os.getenv('PAGE_LIMIT')

class TestConfig(Config):
    LOG_LEVEL = "DEBUG"
    MONGO_TEST_URI = os.getenv('MONGO_TEST_URI')
    MONGO_TESTDB_NAME = os.getenv('MONGO_TESTDB_NAME')
