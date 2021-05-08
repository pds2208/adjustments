import time
from datetime import datetime

from persistence import session_scope
from persistence.adjustments import get_sage_stats, get_sage_adjustment
from persistence.models import AdjustmentType
from sage import SageException
from sage.cost_price import get_sage_cost_price
from sage.sage_stock import update_sage_stock
from util.configuration import sleep, get_cost_price
from util.logging import log


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

        if get_cost_price is True:
            try:
                cost = get_sage_cost_price(adj.stock_code)
                if cost is None:
                    log.info(f"Cost price for {adj.stock_code} not found - does the product exist?")
                else:
                    log.info(f"Cost price for {adj.stock_code} is {cost}")
            except SageException:
                return
        else:
            cost = None

        result = update_sage_stock(
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
            return

        adj.num_retries = adj.num_retries + 1
        sage_stats.total_failures = sage_stats.total_failures + 1
        session.add(adj)
        session.add(sage_stats)
        log.warning(f"Update Sage record for product {adj.stock_code} FAILED, {result}")


if __name__ == "__main__":
    while True:
        update_sage()
        time.sleep(sleep)
