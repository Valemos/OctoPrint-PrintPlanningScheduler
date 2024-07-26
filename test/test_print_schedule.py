from datetime import datetime, timedelta
from octoprint_print_planning_scheduler.printing_schedule.print_schedule import (
    PrintSchedule,
)


def test_new_schedule_allows_all_prints():

    # Usage Example:
    scheduler = PrintSchedule("path/to/your/calendar.ics")

    # Adding urgent outage
    urgent_start = datetime(2024, 7, 4, 14, 0)  # Example urgent outage start time
    urgent_end = datetime(2024, 7, 4, 18, 0)  # Example urgent outage end time
    scheduler.add_urgent_outage(urgent_start, urgent_end)

    # Adding jobs with fixed execution time
    scheduler.add_job(timedelta(hours=1))
    scheduler.add_job(timedelta(hours=2))
    scheduler.add_job(timedelta(minutes=30))

    # Scheduling jobs
    scheduled_jobs = scheduler.schedule_jobs()
    print("Scheduled Jobs:", scheduled_jobs)
