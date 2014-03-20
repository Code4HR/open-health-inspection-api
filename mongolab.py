import config
from pymongo import MongoClient

def connect():
    c = config.load()
    client = MongoClient(c["db_uri"])
    return client[c["db_name"]]