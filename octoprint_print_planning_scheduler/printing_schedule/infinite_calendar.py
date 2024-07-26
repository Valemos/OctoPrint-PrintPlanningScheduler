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

    def generate_intervals(self, period: DateInterval) -> DateIntervalSet:
        intervals = DateIntervalSet()
        for occurrence in self.recurrence.between(period.start, period.end, inc=True):
            occurrence_end = occurrence + (self.end - self.start)
            intervals.add(DateInterval(occurrence, occurrence_end))
        return intervals


@dataclass
class SingleEvent:
    start: datetime
    end: datetime

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
    def from_file(cls, file_path: Path) -> "InfiniteCalendar":
        with open(file_path, "r") as f:
            gcal = Calendar.from_ical(f.read())
            events = []
            for component in gcal.walk():
                if component.name == "VEVENT":
                    start = component.get("dtstart").dt
                    end = component.get("dtend").dt
                    recurrence = component.get("rrule", None)
                    if recurrence is not None:
                        events.append(
                            RecurringEvent(
                                start,
                                end,
                                rrulestr(recurrence.to_ical().decode("utf-8")),
                            )
                        )
                    else:
                        events.append(SingleEvent(start, end))
            return InfiniteCalendar(sorted(events, key=lambda e: e.start))

    def generate_intervals_for_period(self, interval: DateInterval) -> DateIntervalSet:
        total_intervals_set = DateIntervalSet()
        for event in self.events:
            intervals = event.generate_intervals(interval)
            total_intervals_set.extend(intervals)
        return total_intervals_set
