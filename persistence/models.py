import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class AdjustmentType(enum.Enum):
    adj_in = "adj_in"
    adj_out = "adj_out"


SQLModel.metadata.schema = "stock"


class Adjustments(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    adjustment_type: AdjustmentType
    amount: Decimal
    stock_code: str
    reference_text: str
    sage_updated: bool
    inserted_at: datetime
    sage_updated_at: datetime
    num_retries: int
    updates_paused: bool
    paused_time: datetime


class SageStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    total_updated: int
    total_failures: int
    paused: bool
