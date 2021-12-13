from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from persistence.models import Adjustments, SageStats


def get_paused_adjustments(session: Session) -> list[Adjustments]:
    return session.query(Adjustments).filter(
        Adjustments.updates_paused == 1
    ).all()


def get_next_adjustment(session: Session) -> Optional[Adjustments]:
    return session.query(Adjustments).filter(
        Adjustments.sage_updated == 0 and Adjustments.updates_paused == 0
    ).first()


def update_adjustment(session: Session, adjustment: Adjustments) -> None:
    session.add(adjustment)


def get_sage_stats(session: Session) -> SageStats:
    a = session.query(SageStats).one()
    return a


def update_sage_stats(session: Session, stats: SageStats) -> None:
    session.add(stats)

