from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import timedelta, datetime

from dataclasses_json import dataclass_json

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


@dataclass_json
@dataclass
class PrintScheduleModel:
    calendar: InfiniteCalendar = field(default_factory=InfiniteCalendar)
    excluded_intervals: DateIntervalSet = field(default_factory=DateIntervalSet)
    jobs: list[PrintJob] = field(default_factory=list)

    def __post_init__(self):
        self._last_job_id = 0

    def add_job(self, job: PrintJob):
        self._last_job_id += 1
        job._id = self._last_job_id
        self.jobs.append(job)
        return self._last_job_id

    def remove_job(self, job_id: int):
        before_count = len(self.jobs)
        self.jobs = list(filter(lambda j: j._id == job_id, self.jobs))
        return before_count - len(self.jobs)


class PrintSchedule:
    def __init__(self):
        self._model = PrintScheduleModel()

    @property
    def calendar(self):
        return self._model.calendar

    @calendar.setter
    def calendar(self, value):
        self._model.calendar = value

    @property
    def excluded_intervals(self):
        return self._model.excluded_intervals

    @property
    def jobs(self):
        return self._model.jobs

    @jobs.setter
    def jobs(self, value):
        self._model.jobs = value

    @classmethod
    def from_ical(cls, ical_file: Path):
        obj = cls()
        obj.calendar = InfiniteCalendar.from_ical(ical_file)
        return obj

    def reset(self):
        self._model.excluded_intervals = DateIntervalSet()

    def add_job(self, job: PrintJob):
        return self._model.add_job(job)

    def remove_job(self, job_id):
        return self._model.remove_job(job_id)

    def add_exclusion_interval(self, interval: DateInterval):
        self.excluded_intervals.add(interval)

    def get_available_intervals(
        self, start_time: datetime, max_duration: timedelta
    ) -> DateIntervalSet:
        target_period = DateInterval(start_time, start_time + max_duration)
        disabled = self.calendar.generate_intervals_for_period(target_period)
        disabled = disabled.subtract(self.excluded_intervals)
        return disabled.get_inverted_intervals(target_period)

    def get_scheduled_job_options(self, start_time: datetime) -> list[PrintJob]:
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
