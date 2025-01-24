import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "")
    ASYNC_SQLALCHEMY_DATABASE_URL = os.getenv("ASYNC_SQLALCHEMY_DATABASE_URL", "")
    API_TOKEN = os.getenv("API_TOKEN", "")
