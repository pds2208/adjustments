from sqlmodel import create_engine

from util.configuration import database_uri

engine = create_engine(database_uri)
conn = engine.connect()
