from dataclasses import dataclass, field
from datetime import datetime, timedelta
from bisect import bisect_left, bisect_right

from .date_interval import DateInterval


@dataclass
class DateIntervalSet:
    intervals: list[DateInterval] = field(default_factory=list)

    def __post_init__(self):
        initial_intervals = self.intervals
        self.intervals = []
        for interval in initial_intervals:
            self.add(interval)

    def add(self, new_interval: DateInterval):
        # Insert and merge intervals
        self.intervals.append(new_interval)
        self.intervals.sort(key=lambda interval: interval.start)
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

    def extend(self, interval_set: "DateIntervalSet"):
        for interval in interval_set.intervals:
            self.add(interval)

    def remove_interval(self, remove_interval: DateInterval):
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

    def get_inverted_intervals(self, start: datetime, end: datetime):
        result = []
        previous_end = start
        for interval in self.intervals:
            if interval.start > previous_end:
                result.append(DateInterval(previous_end, interval.start))
            previous_end = max(previous_end, interval.end)
        if previous_end < end:
            result.append(DateInterval(previous_end, end))
        return result

    def find_closest_future_interval(self, dt: datetime):
        if not self.intervals:
            return None
        starts = [interval.start for interval in self.intervals]
        idx = bisect_right(starts, dt)
        if idx < len(self.intervals):
            return self.intervals[idx]
        return None
