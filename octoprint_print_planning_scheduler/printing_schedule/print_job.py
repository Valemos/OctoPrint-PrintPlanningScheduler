from dataclasses import dataclass
from datetime import timedelta


@dataclass
class PrintJob:
    name: str
    duration: timedelta
    description: str = ""
    _id: int = 0
