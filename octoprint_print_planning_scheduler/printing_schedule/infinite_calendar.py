from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from icalendar import Calendar
from datetime import datetime, timedelta
from dateutil.rrule import rrule, rruleset, rrulestr

from octoprint_print_planning_scheduler.printing_schedule.date_interval import (
    DateInterval,
)
from octoprint_print_planning_scheduler.printing_schedule.date_interval_set import (
    DateIntervalSet,
)


@dataclass
class RecurringEvent:
    start: datetime
    end: datetime
    recurrence: rrule | rruleset
    stop_date: datetime | None = None
    name: str | None = None

    def generate_intervals(self, period: DateInterval) -> DateIntervalSet:
        intervals = DateIntervalSet()
        duration = self.end - self.start
        period_end = min(period.end, self.stop_date) if self.stop_date else period.end
        for occurrence in self.recurrence.between(period.start, period_end, inc=True):
            occurrence_end = occurrence + duration
            intervals.add(DateInterval(occurrence, occurrence_end))
        return intervals


@dataclass
class SingleEvent:
    start: datetime
    end: datetime
    name: str = ""

    def generate_intervals(self, period: DateInterval) -> DateIntervalSet:
        if self.start < period.end and self.end > period.start:
            return DateIntervalSet(
                [DateInterval(max(self.start, period.start), min(self.end, period.end))]
            )
        return DateIntervalSet()


class InfiniteCalendar:
    def __init__(self, events: list[SingleEvent | RecurringEvent] | None = None):
        self.events = events if events else []

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
                            start.dt,
                            end.dt,
                            rrulestr(f"DTSTART:{start_str}\nRRULE:{recurrence_str}"),
                        )
                    )
                else:
                    events.append(SingleEvent(start.dt, end.dt))
        return InfiniteCalendar(sorted(events, key=lambda e: e.start))

    def add_event(
        self,
        start: datetime,
        end: datetime,
        name: str | None = None,
        recurrence: rrule | rruleset | None = None,
        stop_date: datetime | None = None,
    ):
        if recurrence is None:
            self.events.append(SingleEvent(start, end, name))
        else:
            self.events.append(RecurringEvent(start, end, recurrence, stop_date, name))

    def generate_intervals_for_period(self, interval: DateInterval) -> DateIntervalSet:
        total_intervals_set = DateIntervalSet()
        for event in self.events:
            intervals = event.generate_intervals(interval)
            total_intervals_set.extend(intervals)
        return total_intervals_set

    def get_intervals_as_events_for_period(
        self, interval: DateInterval
    ) -> list[SingleEvent]:
        total_events = []
        for event in self.events:
            intervals = event.generate_intervals(interval)
            total_events.extend(
                map(lambda i: SingleEvent(i.start, i.end, event.name), intervals)
            )
        return total_events
