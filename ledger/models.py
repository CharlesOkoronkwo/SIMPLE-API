from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class Account:
    id: int
    name: str
    layout: str
    opening_balance: float
    currency: str
    created_at: str

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            name=row["name"],
            layout=row["layout"],
            opening_balance=row["opening_balance"],
            currency=row["currency"],
            created_at=row["created_at"],
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class Transaction:
    id: int
    account_id: int
    posted_on: str
    description: str
    amount: float
    reference: Optional[str]
    category: Optional[str]
    source_file: Optional[str]

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            account_id=row["account_id"],
            posted_on=row["posted_on"],
            description=row["description"],
            amount=row["amount"],
            reference=row["reference"],
            category=row["category"],
            source_file=row["source_file"],
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class ParsedRow:
    """One statement line after a layout has read it."""

    posted_on: str
    description: str
    amount: float
    reference: Optional[str] = None
    balance: Optional[float] = None


@dataclass
class ImportResult:
    filename: str
    layout: str
    rows_read: int = 0
    rows_added: int = 0
    rows_skipped: int = 0
    problems: Optional[List[str]] = None

    def to_dict(self):
        data = asdict(self)
        data["problems"] = list(self.problems or [])
        return data
