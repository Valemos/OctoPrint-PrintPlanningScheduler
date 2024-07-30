import pytest
from datetime import datetime

from octoprint_print_planning_scheduler.printing_schedule.date_interval import (
    DateInterval,
)
from octoprint_print_planning_scheduler.printing_schedule.date_interval_set import (
    DateIntervalSet,
)


def test_add_interval_no_overlap():
    interval_set = DateIntervalSet()
    interval_set.add(DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 10)))
    interval_set.add(DateInterval(datetime(2023, 1, 15), datetime(2023, 1, 20)))
    assert len(interval_set.intervals) == 2


def test_add_interval_with_overlap():
    interval_set = DateIntervalSet()
    interval_set.add(DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 10)))
    interval_set.add(DateInterval(datetime(2023, 1, 5), datetime(2023, 1, 15)))
    assert len(interval_set.intervals) == 1
    assert interval_set.intervals[0] == DateInterval(
        datetime(2023, 1, 1), datetime(2023, 1, 15)
    )


def test_add_interval_contiguous():
    interval_set = DateIntervalSet()
    interval_set.add(DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 10)))
    interval_set.add(DateInterval(datetime(2023, 1, 10), datetime(2023, 1, 20)))
    assert len(interval_set.intervals) == 1
    assert interval_set.intervals[0] == DateInterval(
        datetime(2023, 1, 1), datetime(2023, 1, 20)
    )


def test_remove_interval_completely_within():
    interval_set = DateIntervalSet()
    interval_set.add(DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 20)))
    interval_set.remove_interval(
        DateInterval(datetime(2023, 1, 5), datetime(2023, 1, 15))
    )
    assert len(interval_set.intervals) == 2
    assert interval_set.intervals[0] == DateInterval(
        datetime(2023, 1, 1), datetime(2023, 1, 5)
    )
    assert interval_set.intervals[1] == DateInterval(
        datetime(2023, 1, 15), datetime(2023, 1, 20)
    )


def test_remove_interval_partial_overlap_start():
    interval_set = DateIntervalSet()
    interval_set.add(DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 10)))
    interval_set.remove_interval(
        DateInterval(datetime(2022, 12, 25), datetime(2023, 1, 5))
    )
    assert len(interval_set.intervals) == 1
    assert interval_set.intervals[0] == DateInterval(
        datetime(2023, 1, 5), datetime(2023, 1, 10)
    )


def test_remove_interval_partial_overlap_end():
    interval_set = DateIntervalSet()
    interval_set.add(DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 10)))
    interval_set.remove_interval(
        DateInterval(datetime(2023, 1, 5), datetime(2023, 1, 15))
    )
    assert len(interval_set.intervals) == 1
    assert interval_set.intervals[0] == DateInterval(
        datetime(2023, 1, 1), datetime(2023, 1, 5)
    )


def test_remove_big_interval_with_partial_and_complete_overlaps():
    interval_set = DateIntervalSet()
    interval_set.add(
        DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 10))
    )  # Interval 1
    interval_set.add(
        DateInterval(datetime(2023, 1, 15), datetime(2023, 1, 20))
    )  # Interval 2
    interval_set.add(
        DateInterval(datetime(2023, 1, 25), datetime(2023, 2, 1))
    )  # Interval 3

    big_interval = DateInterval(datetime(2023, 1, 5), datetime(2023, 1, 30))
    interval_set.remove_interval(big_interval)

    remaining_intervals = interval_set.intervals
    assert len(remaining_intervals) == 2
    assert remaining_intervals[0] == DateInterval(
        datetime(2023, 1, 1), datetime(2023, 1, 5)
    )  # Remaining part of Interval 1
    assert remaining_intervals[1] == DateInterval(
        datetime(2023, 1, 30), datetime(2023, 2, 1)
    )  # Remaining part of Interval 3


def test_remove_interval_no_overlap():
    interval_set = DateIntervalSet()
    interval_set.add(DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 10)))
    interval_set.remove_interval(
        DateInterval(datetime(2023, 1, 11), datetime(2023, 1, 20))
    )
    assert len(interval_set.intervals) == 1
    assert interval_set.intervals[0] == DateInterval(
        datetime(2023, 1, 1), datetime(2023, 1, 10)
    )


def test_get_negated_intervals():
    interval_set = DateIntervalSet()
    interval_set.add(DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 10)))
    interval_set.add(DateInterval(datetime(2023, 1, 15), datetime(2023, 1, 20)))
    negated_intervals = interval_set.get_inverted_intervals(
        DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 20))
    )
    assert len(negated_intervals.intervals) == 1
    assert negated_intervals.intervals[0] == DateInterval(
        datetime(2023, 1, 10), datetime(2023, 1, 15)
    )


def test_find_closest_future_interval():
    interval_set = DateIntervalSet()
    interval_set.add(DateInterval(datetime(2023, 1, 1), datetime(2023, 1, 10)))
    interval_set.add(DateInterval(datetime(2023, 1, 15), datetime(2023, 1, 20)))
    closest_interval = interval_set.find_closest_future_interval(datetime(2023, 1, 12))
    assert closest_interval == DateInterval(
        datetime(2023, 1, 15), datetime(2023, 1, 20)
    )
