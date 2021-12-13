from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from persistence import session_scope
from persistence.adjustments import get_next_adjustment, get_sage_stats, update_adjustment, get_paused_adjustments
from persistence.models import AdjustmentType, Adjustments
from sage import SageException
from sage.cost_price import get_sage_cost_price
from sage.sage_stock import update_sage_stock
from util.configuration import get_cost_price, adjustment_pause
from util.logging import log


@dataclass
class Result:
    sage_failed: bool = False
    stock_code: str = None
    error: str = None


def get_reference(ref: str) -> str:
    match ref:
        case "CFA" | "Cutting":
            return "C"
        case "Measurement":
            return "M"
        case "Sampling":
            return "S"
        case "Adjustments":
            return "ADJ"
        case _:
            return ref


def pause_adjustment(adjustment: Adjustments) -> None:
    with session_scope() as session:
        adjustment.updates_paused = True
        adjustment.paused_time = datetime.now()
        update_adjustment(session, adjustment)


def resume_paused_adjustments() -> None:
    with session_scope() as session:
        adjustments = get_paused_adjustments(session)
        for a in adjustments:
            now = datetime.now()
            c = a.paused_time - now
            minutes = c.total_seconds()
            if minutes > adjustment_pause:
                a.updates_paused = False
                update_adjustment(session, a)


def update_sage() -> Tuple[Adjustments | None, Result]:
    with session_scope() as session:
        resume_paused_adjustments()
        sage_stats = get_sage_stats(session)

        if sage_stats.paused == 1:
            log.info("Adjustments are paused, skipping")
            return None, Result()

        adjustment = get_next_adjustment(session)

        if adjustment is None:
            # log.info("No adjustment(s) to process")
            return None, Result()

        log.info(f"Processing adjustment: {adjustment.stock_code}")

        if get_cost_price is True:
            try:
                cost = get_sage_cost_price(adjustment.stock_code)
                if cost is None:
                    log.info(f"Cost price for {adjustment.stock_code} not found - does the product exist?")
                else:
                    log.info(f"Cost price for {adjustment.stock_code} is {cost}")
            except SageException as e:
                return adjustment, Result(sage_failed=True, stock_code=adjustment.stock_code, error=e.message)
        else:
            cost = None

        try:
            result: Optional[str] = update_sage_stock(
                adj_type=1 if adjustment.adjustment_type.name == AdjustmentType.adj_in.name else 2,
                quantity=adjustment.amount,
                stock_code=adjustment.stock_code,
                reference=get_reference(adjustment.reference_text),
                batch=adjustment.batch,
                cost=cost
            )
        except Exception as e:
            result = str(e)

        if result is None:
            adjustment.sage_updated = True
            adjustment.sage_updated_at = datetime.now()
            session.add(adjustment)
            sage_stats.total_updated = sage_stats.total_updated + 1
            session.add(sage_stats)
            log.info(f"Updated Sage record for product {adjustment.stock_code}")
            return adjustment, Result()

        adjustment.num_retries = adjustment.num_retries + 1
        sage_stats.total_failures = sage_stats.total_failures + 1
        session.add(adjustment)
        session.add(sage_stats)
        log.warning(f"Update Sage record for product {adjustment.stock_code} FAILED, {result}")
        return adjustment, Result(sage_failed=True, stock_code=adjustment.stock_code, error=result)
