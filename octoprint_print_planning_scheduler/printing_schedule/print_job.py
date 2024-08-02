from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from dataclasses_json import DataClassJsonMixin, config


@dataclass
class PrintJob(DataClassJsonMixin):
    name: str
    duration: timedelta = field(
        metadata=config(
            decoder=lambda seconds: timedelta(seconds=seconds),
            encoder=lambda td: td.seconds,
        )
    )
    description: str = ""
    _id: int = 0
