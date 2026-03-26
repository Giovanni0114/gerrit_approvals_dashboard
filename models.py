from dataclasses import dataclass


@dataclass
class Change:
    host: str
    hash: str
    waiting: bool = False
    deleted: bool = False
    disabled: bool = False
