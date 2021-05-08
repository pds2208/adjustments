from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from util.configuration import database_uri

uri = database_uri
engine = create_engine(uri)
conn = engine.connect()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
