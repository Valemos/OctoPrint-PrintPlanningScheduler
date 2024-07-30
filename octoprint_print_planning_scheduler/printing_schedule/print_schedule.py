from __future__ import annotations

from typing import List, Optional
from pathlib import Path
from datetime import timedelta, datetime

from octoprint_print_planning_scheduler.printing_schedule.date_interval import (
    DateInterval,
)
from octoprint_print_planning_scheduler.printing_schedule.date_interval_set import (
    DateIntervalSet,
)
from octoprint_print_planning_scheduler.printing_schedule.infinite_calendar import (
    InfiniteCalendar,
)
from octoprint_print_planning_scheduler.printing_schedule.print_job import PrintJob


class PrintSchedule:
    def __init__(self, calendar: InfiniteCalendar):
        self._calendar = calendar
        self._excluded_intervals = DateIntervalSet()
        self.jobs: List[PrintJob] = []

    @property
    def calendar(self):
        return self._calendar

    @calendar.setter
    def calendar(self, value):
        self._calendar = value

    @classmethod
    def from_ical(cls, ical_file: Path):
        calendar = InfiniteCalendar.from_ical(ical_file)
        return cls(calendar)

    def reset(self):
        self._excluded_intervals = DateIntervalSet()

    def add_job(self, job: PrintJob):
        self.jobs.append(job)

    def add_exclusion_interval(self, interval: DateInterval):
        self._excluded_intervals.add(interval)

    def get_available_intervals(
        self, start_time: datetime, max_duration: timedelta
    ) -> DateIntervalSet:
        target_period = DateInterval(start_time, start_time + max_duration)
        disabled = self._calendar.generate_intervals_for_period(target_period)
        disabled = disabled.subtract(self._excluded_intervals)
        return disabled.get_inverted_intervals(target_period)

    def get_scheduled_job_options(self, start_time: datetime) -> List[PrintJob]:
        if not self.jobs:
            return []

        jobs = list(self.jobs)
        jobs.sort(key=lambda job: job.duration, reverse=True)
        max_job_duration = max(jobs, key=lambda job: job.duration).duration
        available_intervals = self.get_available_intervals(start_time, max_job_duration)

        if len(available_intervals.intervals) == 0:
            return []

        current_interval = available_intervals.intervals[0]
        if current_interval.start != start_time:
            return []

        scheduled_jobs = []
        for job in jobs:
            if current_interval.start + job.duration <= current_interval.end:
                scheduled_jobs.append(job)

        return scheduled_jobs
