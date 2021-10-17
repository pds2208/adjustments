import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import urllib3

from persistence import session_scope
from persistence.adjustments import get_sage_adjustment, get_sage_stats
from persistence.models import AdjustmentType
from sage import SageException
from sage.cost_price import get_sage_cost_price
from sage.sage_stock import update_sage_stock
from send_email import send_email
from util.configuration import get_cost_price, maximum_errors, sleep
from util.logging import log


@dataclass
class Result:
    sage_failed: bool = False
    stock_code: str = None
    error: str = None


def get_reference(ref: str) -> str:
    if ref == "CFA":
        return "C"
    if ref == "Cutting":
        return "C"
    if ref == "Measurement":
        return "M"
    if ref == "Sampling":
        return "S"
    if ref == "Adjustments":
        return "ADJ"
    return ref


def update_sage() -> Result:
    with session_scope() as session:
        sage_stats = get_sage_stats(session)

        if sage_stats.paused == 1:
            log.info("Adjustments are paused, skipping")
            return Result()

        adj = get_sage_adjustment(session)

        if adj is None:
            # log.info("No adjustment(s) to process")
            return Result()

        log.info(f"Processing adjustment: {adj.stock_code}")

        if get_cost_price is True:
            try:
                cost = get_sage_cost_price(adj.stock_code)
                if cost is None:
                    log.info(f"Cost price for {adj.stock_code} not found - does the product exist?")
                else:
                    log.info(f"Cost price for {adj.stock_code} is {cost}")
            except SageException as e:
                return Result(sage_failed=True, stock_code=adj.stock_code, error=e.message)
        else:
            cost = None

        try:
            result: Optional[str] = update_sage_stock(
                adj_type=1 if adj.adjustment_type.name == AdjustmentType.adj_in.name else 2,
                quantity=adj.amount,
                stock_code=adj.stock_code,
                adjustment_date=adj.adjustment_date,
                reference=get_reference(adj.reference_text),
                batch=adj.batch,
                cost=cost
            )
        except Exception as e:
            result = str(e)

        if result is None:
            adj.sage_updated = True
            adj.sage_updated_at = datetime.now()
            session.add(adj)
            sage_stats.total_updated = sage_stats.total_updated + 1
            session.add(sage_stats)
            log.info(f"Updated Sage record for product {adj.stock_code}")
            return Result()

        adj.num_retries = adj.num_retries + 1
        sage_stats.total_failures = sage_stats.total_failures + 1
        session.add(adj)
        session.add(sage_stats)
        log.warning(f"Update Sage record for product {adj.stock_code} FAILED, {result}")
        return Result(sage_failed=True, stock_code=adj.stock_code, error=result)


if __name__ == "__main__":
    num_errors = 0
    send_email_on_error = True

    urllib3.disable_warnings()
    time.sleep(15)

    while True:
        res: Result = update_sage()
        if res.sage_failed:
            num_errors = num_errors + 1
            if num_errors > maximum_errors and send_email_on_error:
                log.warning(
                    f"{maximum_errors} errors have occurred. Sending email alert..."
                )
                send_email(res.stock_code, res.error)
                send_email_on_error = False
        else:
            num_errors = 0
            send_email_on_error = True

        time.sleep(sleep)
