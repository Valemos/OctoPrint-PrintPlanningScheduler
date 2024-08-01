from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from bisect import bisect_left, bisect_right

from dataclasses_json import DataClassJsonMixin

from .date_interval import DateInterval


@dataclass
class DateIntervalSet(DataClassJsonMixin):
    intervals: list[DateInterval] = field(default_factory=list)

    def __post_init__(self):
        initial_intervals = self.intervals
        self.intervals = []
        for interval in sorted(initial_intervals, key=lambda interval: interval.start):
            self.add(interval)

    def __iter__(self):
        return iter(self.intervals)

    def add(self, new_interval: DateInterval):
        index = bisect_left(
            [interval.start for interval in self.intervals], new_interval.start
        )
        self.intervals.insert(index, new_interval)

        merged_intervals = []
        current = self.intervals[0]
        for interval in self.intervals[1:]:
            if current.end >= interval.start:  # overlap or contiguous
                current = DateInterval(current.start, max(current.end, interval.end))
            else:
                merged_intervals.append(current)
                current = interval
        merged_intervals.append(current)
        self.intervals = merged_intervals

    def remove(self, remove_interval: DateInterval):
        new_intervals = []
        for interval in self.intervals:
            if (
                remove_interval.start <= interval.start
                and remove_interval.end >= interval.end
            ):
                continue  # interval completely removed
            elif (
                remove_interval.start > interval.end
                or remove_interval.end < interval.start
            ):
                new_intervals.append(interval)  # no overlap
            else:
                # partial overlaps
                if remove_interval.start > interval.start:
                    new_intervals.append(
                        DateInterval(interval.start, remove_interval.start)
                    )
                if remove_interval.end < interval.end:
                    new_intervals.append(
                        DateInterval(remove_interval.end, interval.end)
                    )
        self.intervals = new_intervals

    def get_intervals_within(self, given_interval: DateInterval) -> "DateIntervalSet":
        result = DateIntervalSet()
        for interval in self.intervals:
            if interval.end <= given_interval.start:
                continue
            if interval.start >= given_interval.end:
                break
            start = max(interval.start, given_interval.start)
            end = min(interval.end, given_interval.end)
            result.add(DateInterval(start, end))
        return result

    def subtract(self, interval_set: "DateIntervalSet"):
        result = copy.deepcopy(self)
        for interval in interval_set.intervals:
            result.remove(interval)
        return result

    def extend(self, interval_set: "DateIntervalSet"):
        for interval in interval_set.intervals:
            self.add(interval)

    def get_inverted_intervals(self, period: DateInterval):
        result = DateIntervalSet()
        previous_end = period.start
        for interval in self.intervals:
            if interval.start > previous_end:
                result.add(DateInterval(previous_end, interval.start))
            previous_end = max(previous_end, interval.end)
        if previous_end < period.end:
            result.add(DateInterval(previous_end, period.end))
        return result

    def find_closest_future_interval(self, dt: datetime):
        if not self.intervals:
            return None
        starts = [interval.start for interval in self.intervals]
        idx = bisect_right(starts, dt)
        if idx < len(self.intervals):
            return self.intervals[idx]
        return None
