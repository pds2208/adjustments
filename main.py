import time
from datetime import datetime
from typing import Optional

from persistence import session_scope
from persistence.adjustments import get_sage_adjustment, get_sage_stats
from persistence.models import AdjustmentType
from sage import SageException
from sage.cost_price import get_sage_cost_price
from sage.sage_stock import update_sage_stock
from send_email import send_email
from util.configuration import get_cost_price, maximum_errors, sleep
from util.logging import log


class Result:
    stock_code: str
    error: str
    sage_failed: bool

    def __init__(self, sage_failed: bool = False, error: Optional[str] = None, stock_code: Optional[str] = None):
        self.sage_failed = sage_failed
        self.error = error
        self.stock_code = stock_code


def update_sage() -> Result:
    with session_scope() as session:
        sage_stats = get_sage_stats(session)

        if sage_stats.paused == 1:
            log.info("Adjustments are paused, skipping")
            return Result()

        adj = get_sage_adjustment(session)

        if adj is None:
            log.info("No adjustment(s) to process")
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
                return Result(True, e.message, adj.stock_code)
        else:
            cost = None

        result: Optional[str] = update_sage_stock(
                adj_type=1 if adj.adjustment_type.name == AdjustmentType.adj_in.name else 2,
                quantity=adj.amount,
                stock_code=adj.stock_code,
                reference=adj.reference_text,
                cost=cost
                )

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
        return Result(True, result, adj.stock_code)


if __name__ == "__main__":
    num_errors = 0
    send_email_on_error = False

    while True:
        result: Result = update_sage()
        if result.sage_failed:
            num_errors = num_errors + 1
            if num_errors > maximum_errors and send_email_on_error:
                log.warning(
                        f"{maximum_errors} has occurred while sending adjustment for: {result.stock_code}. Sending email alert..."
                        )
                send_email(result.stock_code, result.error)
                send_email_on_error = False
        else:
            num_errors = 0
            send_email_on_error = True

        time.sleep(sleep)
