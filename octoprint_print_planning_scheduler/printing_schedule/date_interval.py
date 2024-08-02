from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from dataclasses_json import DataClassJsonMixin


_DATE_FORMAT = "%Y-%m-%dT%H-%M"


@dataclass(unsafe_hash=True)
class DateInterval(DataClassJsonMixin):
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.start.tzinfo is None:
            self.start = self.start.replace(tzinfo=timezone.utc)
        if self.end.tzinfo is None:
            self.end = self.end.replace(tzinfo=timezone.utc)

    def __contains__(self, value):
        return self.start <= value <= self.end

    @property
    def duration(self):
        return self.end - self.start

    def get_str(self):
        return (
            f"{self.start.strftime(_DATE_FORMAT)} - {self.end.strftime(_DATE_FORMAT)}"
        )
