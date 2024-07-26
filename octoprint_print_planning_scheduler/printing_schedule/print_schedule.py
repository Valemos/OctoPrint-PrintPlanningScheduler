from __future__ import annotations

import datetime
from icalendar import Calendar
from datetime import timedelta, datetime


class PrintSchedule:
    def __init__(self, ical_file):
        self.ical_file = ical_file
        self.power_intervals = []
        self.jobs = []
        self.load_ical()

    def load_ical(self):
        with open(self.ical_file, "rb") as f:
            gcal = Calendar.from_ical(f.read())
            outages = []
            for component in gcal.walk():
                if component.name == "VEVENT":
                    start = component.get("dtstart").dt
                    end = component.get("dtend").dt
                    outages.append((start, end))

            outages.sort()
            self.calculate_power_intervals(outages)

    def calculate_power_intervals(self, outages):
        current_time = datetime.now()
        for start, end in outages:
            if start > current_time:
                self.power_intervals.append((current_time, start))
            current_time = end
        if current_time < datetime.now() + timedelta(
            days=1
        ):  # Assuming 24-hour scheduling window
            self.power_intervals.append(
                (current_time, datetime.now() + timedelta(days=1))
            )

    def add_urgent_outage(self, start, end):
        self.power_intervals = []
        self.calculate_power_intervals([(start, end)])

    def add_job(self, job_duration):
        self.jobs.append(job_duration)

    def schedule_jobs(self):
        scheduled_jobs = []
        for job_duration in self.jobs:
            for i, (start, end) in enumerate(self.power_intervals):
                if end - start >= job_duration:
                    scheduled_jobs.append((start, start + job_duration))
                    self.power_intervals[i] = (start + job_duration, end)
                    break
        return scheduled_jobs
