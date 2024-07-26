from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from unittest.mock import mock_open, patch

from pytest import fixture

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
    rrulestr,
)

ICAL_DATETIME_FORMAT = "%Y%m%dT%H%M%S"


@fixture
def calendar_test_data():
    recurring = DateInterval(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 11, 0))
    single = DateInterval(datetime(2024, 7, 1, 15, 0), datetime(2024, 7, 1, 15, 30))
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "BEGIN:VEVENT\r\n"
        f"DTSTART:{recurring.start.strftime(ICAL_DATETIME_FORMAT)}\r\n"
        f"DTEND:{recurring.end.strftime(ICAL_DATETIME_FORMAT)}\r\n"
        "RRULE:FREQ=DAILY;INTERVAL=1\r\n"
        "END:VEVENT\r\n"
        "BEGIN:VEVENT\r\n"
        f"DTSTART:{single.start.strftime(ICAL_DATETIME_FORMAT)}\r\n"
        f"DTEND:{single.end.strftime(ICAL_DATETIME_FORMAT)}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def test_single_event_within_period():
    single_event = SingleEvent(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 12, 0))
    interval_set = single_event.generate_intervals(
        DateInterval(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 1, 13, 0))
    )

    expected_interval = DateInterval(
        datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 12, 0)
    )
    assert interval_set.intervals == [expected_interval]


def test_single_event_outside_period():
    single_event = SingleEvent(datetime(2024, 7, 1, 15, 0), datetime(2024, 7, 1, 17, 0))
    interval_set = single_event.generate_intervals(
        DateInterval(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 1, 13, 0))
    )

    assert interval_set.intervals == []


def test_recurring_event_daily():
    # Define the start date and time of the recurring event
    start_date = datetime(2024, 7, 1, 10, 0)
    end_date = datetime(2024, 7, 1, 11, 0)

    # Create an RRULE string for daily recurrence
    rrule_str = (
        f"DTSTART:{start_date.strftime(ICAL_DATETIME_FORMAT)}\n"
        f"RRULE:FREQ=DAILY;INTERVAL=1"
    )

    recurring_event = RecurringEvent(start_date, end_date, rrulestr(rrule_str))
    interval_set = recurring_event.generate_intervals(
        DateInterval(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 5, 12, 0))
    )

    assert interval_set.intervals == [
        DateInterval(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 11, 0)),
        DateInterval(datetime(2024, 7, 2, 10, 0), datetime(2024, 7, 2, 11, 0)),
        DateInterval(datetime(2024, 7, 3, 10, 0), datetime(2024, 7, 3, 11, 0)),
        DateInterval(datetime(2024, 7, 4, 10, 0), datetime(2024, 7, 4, 11, 0)),
        DateInterval(datetime(2024, 7, 5, 10, 0), datetime(2024, 7, 5, 11, 0)),
    ]


def test_recurring_event_weekly_with_specific_day():
    start_date = datetime(2024, 7, 1, 10, 0)
    end_date = datetime(2024, 7, 1, 11, 0)
    rrule_str = (
        f"DTSTART:{start_date.strftime('%Y%m%dT%H%M%S')}\n"
        f"RRULE:FREQ=WEEKLY;BYDAY=MO"
    )

    recurring_event = RecurringEvent(start_date, end_date, rrulestr(rrule_str))
    interval_set = recurring_event.generate_intervals(
        DateInterval(datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 31, 12, 0))
    )

    assert interval_set.intervals == [
        DateInterval(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 11, 0)),
        DateInterval(datetime(2024, 7, 8, 10, 0), datetime(2024, 7, 8, 11, 0)),
        DateInterval(datetime(2024, 7, 15, 10, 0), datetime(2024, 7, 15, 11, 0)),
        DateInterval(datetime(2024, 7, 22, 10, 0), datetime(2024, 7, 22, 11, 0)),
        DateInterval(datetime(2024, 7, 29, 10, 0), datetime(2024, 7, 29, 11, 0)),
    ]


def test_infinite_calendar_from_file(calendar_test_data):
    with patch("builtins.open", mock_open(read_data=calendar_test_data)) as mock_file:
        calendar = InfiniteCalendar.from_file(Path("mock.ics"))
        mock_file().read.assert_called_once()

    assert len(calendar.events) == 2

    recurring_event = calendar.events[0]
    single_event = calendar.events[1]

    assert isinstance(recurring_event, RecurringEvent)
    assert isinstance(single_event, SingleEvent)

    sample_interval = DateInterval(
        datetime(2024, 7, 1, 9, 0), datetime(2024, 7, 4, 12, 0)
    )
    recurring_intervals = recurring_event.generate_intervals(sample_interval)
    assert recurring_intervals.intervals == [
        DateInterval(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 11, 0)),
        DateInterval(datetime(2024, 7, 2, 10, 0), datetime(2024, 7, 2, 11, 0)),
        DateInterval(datetime(2024, 7, 3, 10, 0), datetime(2024, 7, 3, 11, 0)),
        DateInterval(datetime(2024, 7, 4, 10, 0), datetime(2024, 7, 4, 11, 0)),
    ]

    # Validate SingleEvent intervals
    single_intervals = single_event.generate_intervals(sample_interval)
    assert single_intervals.intervals == [
        DateInterval(datetime(2024, 7, 1, 15, 0), datetime(2024, 7, 1, 15, 30))
    ]

    calendar_intervals = calendar.generate_intervals_for_period(sample_interval)
    assert calendar_intervals.intervals == [
        DateInterval(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 11, 0)),
        DateInterval(datetime(2024, 7, 1, 15, 0), datetime(2024, 7, 1, 15, 30)),
        DateInterval(datetime(2024, 7, 2, 10, 0), datetime(2024, 7, 2, 11, 0)),
        DateInterval(datetime(2024, 7, 3, 10, 0), datetime(2024, 7, 3, 11, 0)),
        DateInterval(datetime(2024, 7, 4, 10, 0), datetime(2024, 7, 4, 11, 0)),
    ]
