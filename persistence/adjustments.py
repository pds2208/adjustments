from typing import Optional

from sqlalchemy.orm import Session

from persistence.models import Adjustments, SageStats


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
