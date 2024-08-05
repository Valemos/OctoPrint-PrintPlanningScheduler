from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from dataclasses_json import DataClassJsonMixin, config
from icalendar import Calendar
from datetime import datetime, timedelta, timezone, tzinfo
from dateutil.rrule import rrule, rruleset, rrulestr

from octoprint_print_planning_scheduler.printing_schedule.date_interval import (
    DateInterval,
)
from octoprint_print_planning_scheduler.printing_schedule.date_interval_set import (
    DateIntervalSet,
)


@dataclass
class RecurringEvent(DataClassJsonMixin):
    start: datetime
    end: datetime
    recurrence: rrule | rruleset = field(
        metadata=config(encoder=lambda r: str(r), decoder=lambda r: rrulestr(r))
    )
    name: str = ""
    stop_date: datetime | None = None

    def __post_init__(self):
        self.start = self.start.astimezone(timezone.utc)
        self.end = self.end.astimezone(timezone.utc)
        self.recurrence = self.recurrence.replace(dtstart=self.start)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, RecurringEvent):
            return False
        return (
            self.start == value.start
            and self.end == value.end
            and str(self.recurrence) == str(value.recurrence)
            and self.stop_date == value.stop_date
            and self.name == value.name
        )

    def generate_intervals(self, period: DateInterval) -> DateIntervalSet:
        intervals = DateIntervalSet()
        duration = self.end - self.start
        period_end = min(period.end, self.stop_date) if self.stop_date else period.end
        for occurrence in self.recurrence.between(period.start, period_end, inc=True):
            occurrence_end = occurrence + duration
            intervals.add(DateInterval(occurrence, occurrence_end))
        return intervals


@dataclass
class SingleEvent(DataClassJsonMixin):
    start: datetime
    end: datetime
    name: str = ""

    def __post_init__(self):
        self.start = self.start.astimezone(timezone.utc)
        self.end = self.end.astimezone(timezone.utc)

    def generate_intervals(self, period: DateInterval) -> DateIntervalSet:
        if self.start < period.end and self.end > period.start:
            return DateIntervalSet(
                [DateInterval(max(self.start, period.start), min(self.end, period.end))]
            )
        return DateIntervalSet()


def _events_to_dict(event_list: list[SingleEvent | RecurringEvent]):
    return [
        {"type": event.__class__.__name__, "obj": event.to_dict()}
        for event in event_list
    ]


def _events_from_dict(data_list: list[dict]):
    def _event_from_dict(data):
        if data["type"] == SingleEvent.__name__:
            return SingleEvent.from_dict(data["obj"])
        elif data["type"] == RecurringEvent.__name__:
            return RecurringEvent.from_dict(data["obj"])
        else:
            raise ValueError("Unknown type")

    return list(map(_event_from_dict, data_list))


@dataclass
class InfiniteCalendar(DataClassJsonMixin):
    events: list[SingleEvent | RecurringEvent] = field(
        default_factory=list,
        metadata=config(encoder=_events_to_dict, decoder=_events_from_dict),
    )

    @classmethod
    def from_ical(cls, file_path: Path) -> "InfiniteCalendar":
        with open(file_path, "r") as f:
            return cls.from_ical_str(f.read())

    @classmethod
    def from_ical_str(cls, ical_str):
        gcal = Calendar.from_ical(ical_str)
        events = []
        for component in gcal.walk():
            if component.name == "VEVENT":
                start = component.get("dtstart")
                end = component.get("dtend")
                recurrence = component.get("rrule", None)
                if recurrence is not None:
                    start_str = start.to_ical().decode("utf-8")
                    recurrence_str = recurrence.to_ical().decode("utf-8")
                    events.append(
                        RecurringEvent(
                            start.dt.replace(tzinfo=timezone.utc),
                            end.dt.replace(tzinfo=timezone.utc),
                            rrulestr(f"DTSTART:{start_str}\nRRULE:{recurrence_str}"),
                        )
                    )
                else:
                    events.append(
                        SingleEvent(
                            start.dt.replace(tzinfo=timezone.utc),
                            end.dt.replace(tzinfo=timezone.utc),
                        )
                    )
        return InfiniteCalendar(sorted(events, key=lambda e: e.start))

    def add_event(
        self,
        start: datetime,
        end: datetime,
        name: str = "",
        recurrence: rrule | None = None,
        stop_date: datetime | None = None,
    ):
        if recurrence is None:
            self.events.append(SingleEvent(start, end, name))
        else:
            self.events.append(RecurringEvent(start, end, recurrence, name, stop_date))

    def generate_intervals_for_period(self, interval: DateInterval) -> DateIntervalSet:
        total_intervals_set = DateIntervalSet()
        for event in self.events:
            intervals = event.generate_intervals(interval)
            total_intervals_set.extend(intervals)
        return total_intervals_set

    def get_intervals_as_events_for_period(
        self, interval: DateInterval
    ) -> list[SingleEvent]:
        total_events: list[SingleEvent] = []
        for event in self.events:
            intervals = event.generate_intervals(interval)
            total_events.extend(
                map(lambda i: SingleEvent(i.start, i.end, event.name), intervals)
            )
        return total_events
