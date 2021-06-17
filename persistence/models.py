import enum
from decimal import Decimal

import sqlalchemy
from sqlalchemy import (
    Column,
    DECIMAL,
    Integer,
    String,
    TIMESTAMP,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class AdjustmentType(enum.Enum):
    adj_in = "adj_in"
    adj_out = "adj_out"


class Adjustments(Base):
    __tablename__ = "adjustments"

    id = Column(Integer, primary_key=True)
    adjustment_type = Column(
        sqlalchemy.Enum(AdjustmentType), name="adjustment_type", nullable=False
    )
    amount: Decimal = Column(DECIMAL(8, 2))
    stock_code = Column(String(64), nullable=False)
    reference_text = Column(String(64))
    details = Column(String(64))
    sage_updated = Column(TINYINT(1), nullable=False)
    inserted_at = Column(TIMESTAMP)
    sage_updated_at = Column(TIMESTAMP)
    num_retries = Column(Integer)
    updates_paused = Column(TINYINT(1))
    paused_time = Column(TIMESTAMP)


class SageStats(Base):
    __tablename__ = "sage_stats"

    id = Column(Integer, primary_key=True)
    total_updated = Column(Integer)
    total_failures = Column(Integer)
    paused = Column(Integer)
