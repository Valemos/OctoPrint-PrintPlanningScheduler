import pytest
from datetime import datetime, timedelta
from dateutil.rrule import rrule, HOURLY

from octoprint_print_planning_scheduler.printing_schedule.date_interval import (
    DateInterval,
)
from octoprint_print_planning_scheduler.printing_schedule.date_interval_set import (
    DateIntervalSet,
)
from octoprint_print_planning_scheduler.printing_schedule.infinite_calendar import (
    InfiniteCalendar,
    RecurringEvent,
    SingleEvent,
)
from octoprint_print_planning_scheduler.printing_schedule.print_job import PrintJob
from octoprint_print_planning_scheduler.printing_schedule.print_schedule import (
    PrintSchedule,
    PrintScheduleModel,
)


@pytest.fixture
def infinite_calendar():
    return InfiniteCalendar()


@pytest.fixture
def print_schedule(infinite_calendar):
    schedule = PrintSchedule()
    schedule.calendar = infinite_calendar
    return schedule


def test_add_job(print_schedule: PrintSchedule):
    job = PrintJob(name="Test Job", duration=timedelta(hours=2))
    print_schedule.add_job(job)
    assert print_schedule.jobs == [job]


def test_add_exclusion_interval(print_schedule: PrintSchedule):
    interval = DateInterval(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 12, 0))
    print_schedule.add_exclusion_interval(interval)
    assert interval in print_schedule.excluded_intervals.intervals


def test_reset(print_schedule: PrintSchedule):
    print_schedule.calendar = InfiniteCalendar(
        [SingleEvent(datetime(2024, 7, 1, 11, 0), datetime(2024, 7, 1, 11, 30))]
    )

    interval = DateInterval(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 12, 0))
    print_schedule.add_exclusion_interval(interval)
    print_schedule.reset()
    assert not print_schedule.excluded_intervals.intervals


def test_schedule_jobs_before_interval(print_schedule: PrintSchedule):
    job1 = PrintJob(name="Job 1", duration=timedelta(hours=1))
    job2 = PrintJob(name="Job 2", duration=timedelta(hours=2))
    print_schedule.add_job(job1)
    print_schedule.add_job(job2)

    print_schedule.calendar = InfiniteCalendar(
        [SingleEvent(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 1, 12, 0))]
    )

    scheduled_jobs = print_schedule.get_scheduled_job_options(
        datetime(2024, 7, 1, 6, 0)
    )
    assert len(scheduled_jobs) == 2
    assert scheduled_jobs[0] == job2
    assert scheduled_jobs[1] == job1


def test_schedule_jobs_interval_end(print_schedule: PrintSchedule):
    job1 = PrintJob(name="Job 1", duration=timedelta(hours=1))
    job2 = PrintJob(name="Job 2", duration=timedelta(hours=2))
    print_schedule.add_job(job1)
    print_schedule.add_job(job2)

    print_schedule.calendar = InfiniteCalendar(
        [SingleEvent(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 1, 12, 0))]
    )

    scheduled_jobs = print_schedule.get_scheduled_job_options(
        datetime(2024, 7, 1, 12, 0)
    )
    assert len(scheduled_jobs) == 2
    assert scheduled_jobs[0] == job2
    assert scheduled_jobs[1] == job1


def test_schedule_jobs_with_lacking_time(print_schedule: PrintSchedule):
    job1 = PrintJob(name="Job 1", duration=timedelta(hours=1))
    job2 = PrintJob(name="Job 2", duration=timedelta(hours=2))
    print_schedule.add_job(job1)
    print_schedule.add_job(job2)

    print_schedule.calendar = InfiniteCalendar(
        [SingleEvent(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 1, 12, 0))]
    )

    scheduled_jobs = print_schedule.get_scheduled_job_options(
        datetime(2024, 7, 1, 8, 0)
    )
    assert len(scheduled_jobs) == 1
    assert scheduled_jobs[0] == job1


def test_no_schedule_jobs_inside_disabled_interval(print_schedule: PrintSchedule):
    job1 = PrintJob(name="Job 1", duration=timedelta(hours=1))
    job2 = PrintJob(name="Job 2", duration=timedelta(hours=2))
    print_schedule.add_job(job1)
    print_schedule.add_job(job2)

    print_schedule.calendar = InfiniteCalendar(
        [SingleEvent(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 1, 12, 0))]
    )

    scheduled_jobs = print_schedule.get_scheduled_job_options(
        datetime(2024, 7, 1, 10, 0)
    )
    assert len(scheduled_jobs) == 0


def test_schedule_jobs_with_exclued_disabled_interval(
    print_schedule: PrintSchedule,
):
    job1 = PrintJob(name="Job 1", duration=timedelta(hours=1))
    job2 = PrintJob(name="Job 2", duration=timedelta(hours=2))
    print_schedule.add_job(job1)
    print_schedule.add_job(job2)

    print_schedule.calendar = InfiniteCalendar(
        [SingleEvent(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 1, 12, 0))]
    )
    print_schedule.add_exclusion_interval(
        DateInterval(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 1, 11, 0))
    )

    scheduled_jobs = print_schedule.get_scheduled_job_options(
        datetime(2024, 7, 1, 9, 0)
    )
    assert len(scheduled_jobs) == 2
    assert scheduled_jobs[0] == job2
    assert scheduled_jobs[1] == job1


def test_schedule_jobs_between_recurrint_event(print_schedule: PrintSchedule):
    job1 = PrintJob(name="Job 1", duration=timedelta(hours=1))
    job2 = PrintJob(name="Job 2", duration=timedelta(hours=2))
    print_schedule.add_job(job1)
    print_schedule.add_job(job2)

    print_schedule.calendar = InfiniteCalendar(
        [
            RecurringEvent(
                datetime(2024, 7, 1, 10, 0),
                datetime(2024, 7, 1, 12, 0),
                rrule(
                    freq=HOURLY, dtstart=datetime(2024, 7, 1, 10, 0), interval=4
                ),  # gap between events is 2h
            )
        ]
    )

    scheduled_jobs = print_schedule.get_scheduled_job_options(
        datetime(2024, 7, 1, 16, 0)
    )
    assert len(scheduled_jobs) == 2
    assert scheduled_jobs[0] == job2
    assert scheduled_jobs[1] == job1

    scheduled_jobs = print_schedule.get_scheduled_job_options(
        datetime(2024, 7, 1, 14, 0)
    )
    assert len(scheduled_jobs) == 0


def test_schedule_serialization():
    schedule = PrintSchedule(
        PrintScheduleModel(
            InfiniteCalendar(
                [
                    SingleEvent(
                        datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 12, 0)
                    ),
                    RecurringEvent(
                        datetime(2024, 7, 2, 10, 0),
                        datetime(2024, 7, 2, 12, 0),
                        rrule(
                            freq=HOURLY, dtstart=datetime(2024, 7, 2, 10, 0), interval=4
                        ),
                    ),
                ]
            ),
            DateIntervalSet(
                [DateInterval(datetime(2024, 7, 2, 11, 0), datetime(2024, 7, 2, 13, 0))]
            ),
            [PrintJob("job", timedelta(hours=1), description="Description", _id=3)],
        )
    )

    schedule_str = schedule.to_json()
    restored_schedule = PrintSchedule.from_json(schedule_str)

    assert restored_schedule == schedule
