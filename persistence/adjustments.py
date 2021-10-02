from typing import Optional

from sqlmodel import Session, select

from persistence import engine
from persistence.models import Adjustments, SageStats


def update_adjustment(adj: Adjustments) -> None:
    with Session(engine) as session:
        session.add(adj)


def get_sage_adjustments() -> list[Adjustments]:
    with Session(engine) as session:
        return session.exec(select(Adjustments).filter(Adjustments.sage_updated == 0)).all()


def get_sage_adjustment() -> Optional[Adjustments]:
    with Session(engine) as session:
        return session.exec(select(Adjustments).filter(Adjustments.sage_updated == 0)).first()


def get_sage_stats() -> SageStats:
    with Session(engine) as session:
        return session.exec(select(SageStats)).one()


def update_sage_stats(stats: SageStats) -> None:
    with Session(engine) as session:
        session.add(stats)


def get_all_adjustments() -> list[Adjustments]:
    with Session(engine) as session:
        return session.exec(select(Adjustments)).all()
