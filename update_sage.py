import time
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from typing import Optional

import requests
from requests.exceptions import ConnectTimeout
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from persistence.models import AdjustmentType, Adjustments, SageStats
from util.configuration import database_uri, sleep
from util.configuration import hyper_uri, adjustments_uri, hyper_api_key, hyper_timeout
from util.logging import log

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
    except:
        session.rollback()
        raise
    finally:
        session.close()


def get_sage_adjustments(session: Session) -> list[Adjustments]:
    return session.query(Adjustments).filter(Adjustments.sage_updated == 0).all()


def get_sage_adjustment(session: Session) -> Optional[Adjustments]:
    return session.query(Adjustments).filter(Adjustments.sage_updated == 0).first()


def get_sage_stats(session: Session) -> SageStats:
    a = session.query(SageStats).one()
    return a


def update_sage_stats(session: Session, stats: SageStats) -> None:
    session.add(stats)


def get_all_adjustments(session: Session) -> list[Adjustments]:
    return session.query(Adjustments).all()


def update_sage_stock(*, adj_type: int, quantity: Decimal, stock_code: str, reference: str) -> Optional[str]:
    now = datetime.today()
    payload = {
        "stockCode": stock_code,
        "quantity": float(quantity),
        "type": adj_type,
        "date": now.strftime("%d/%m/%Y"),
        "reference": "Winegum Stock Adjustment",
        "details": reference.strip()
    }

    endpoint = f"{hyper_uri}{adjustments_uri}"
    log.info(f"Calling HyperSage endpoint: {endpoint}")

    try:
        r = requests.post(
            endpoint,
            headers={"AuthToken": hyper_api_key},
            timeout=hyper_timeout,
            json=payload
        )
    except ConnectTimeout:
        log.error("Connection timeout connecting to HyperSage")
        return "Timed out connecting to HyperSage"
    except TimeoutError:
        log.error("Connection timeout connecting to HyperSage")
        return "Timed out communicating with HyperSage"
    except Exception as e:
        log.error(f"Error communicating with HyperSage: {e}")
        return f"Error communicating with HyperSage: {e}"

    if r.status_code != 200:
        if adj_type == AdjustmentType.adj_out:
            err = f"Cannot add an adjustment out to Sage, error status is {r.status_code}"
            log.error(err)
            raise Exception(err + ". The product quantity on Sage may be incorrect")
        err = f"Cannot add an adjustment in to Sage, error status is {r.status_code}"
        log.error(err)
        raise Exception(err)

    i = r.json()

    if i["success"] is False:
        code = i["code"]
        message = i["message"]
        return f"error {code} from HyperSage, message: {message}"

    typ = "In" if adj_type == 1 else "Out"
    log.info(f"Added adjustment: Stock Code: {stock_code}, Type: {typ}, Quantity: {float(quantity)}")
    return None


def update_sage():
    with session_scope() as session:
        sage_stats = get_sage_stats(session)

        if sage_stats.paused == 1:
            log.info("Adjustments are paused, skipping")
            return

        adj = get_sage_adjustment(session)

        if adj is None:
            log.info("No adjustment(s) to process")
            return

        log.info(f"Processing adjustment: {adj.stock_code}")

        result = update_sage_stock(
            adj_type=1 if adj.adjustment_type.name == AdjustmentType.adj_in.name else 2,
            quantity=adj.amount,
            stock_code=adj.stock_code,
            reference=adj.reference_text,
        )

        if result is None:
            adj.sage_updated = True
            adj.sage_updated_at = datetime.now()
            session.add(adj)
            sage_stats.total_updated = sage_stats.total_updated + 1
            session.add(sage_stats)
            log.info(f"Updated Sage record for product {adj.stock_code}")
        else:
            adj.num_retries = adj.num_retries + 1
            sage_stats.total_failures = sage_stats.total_failures + 1
            session.add(adj)
            session.add(sage_stats)
            log.warn(f"Update Sage record for product {adj.stock_code} FAILED, {result}")


if __name__ == "__main__":
    while True:
        update_sage()
        time.sleep(sleep)
