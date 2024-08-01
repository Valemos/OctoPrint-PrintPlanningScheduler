from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


_DATE_FORMAT = "%Y-%m-%dT%H-%M"


@dataclass(unsafe_hash=True)
class DateInterval:
    start: datetime
    end: datetime

    def __contains__(self, value):
        return self.start <= value <= self.end

    @property
    def duration(self):
        return self.end - self.start

    def get_str(self):
        return (
            f"{self.start.strftime(_DATE_FORMAT)} - {self.end.strftime(_DATE_FORMAT)}"
        )
