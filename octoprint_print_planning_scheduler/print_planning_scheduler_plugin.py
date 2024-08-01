from __future__ import annotations

from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
import flask
from flask import Response
import octoprint.plugin

from octoprint_print_planning_scheduler.printing_schedule.date_interval import (
    DateInterval,
)
from octoprint_print_planning_scheduler.printing_schedule.infinite_calendar import (
    InfiniteCalendar,
)
from octoprint_print_planning_scheduler.printing_schedule.print_job import PrintJob
from octoprint_print_planning_scheduler.printing_schedule.print_schedule import (
    PrintSchedule,
    PrintScheduleModel,
)


class PrintPlanningSchedulerPlugin(
    octoprint.plugin.BlueprintPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
):
    _logger: logging.Logger

    def __init__(self):
        super().__init__()
        self._print_schedule = PrintSchedule()

    def on_settings_initialized(self):
        self._load_schedule()

    @property
    def schedule_save_path(self):
        return Path(self.get_plugin_data_folder()) / "schedule.json"

    def _load_schedule(self):
        if self.schedule_save_path.exists():
            self._print_schedule = PrintSchedule.load(self.schedule_save_path)
        else:
            self._print_schedule = PrintSchedule()

    def _save_schedule(self):
        self._print_schedule.save(self.schedule_save_path)

    def set_calendar_from_file(self, path: Path):
        if path.exists():
            os.remove(self.schedule_save_path)
            os.rename(path, self.schedule_save_path)
            self._print_schedule.calendar = InfiniteCalendar.from_ical(
                self.schedule_save_path
            )
            self._save_schedule()

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return {
            # put your plugin's default settings here
        }

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": [
                "js/print_planning_scheduler.js",
                "js/fullcalendar/dist/index.global.js",
            ],
            "css": ["css/print_planning_scheduler.css"],
            "less": ["less/print_planning_scheduler.less"],
        }

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "print_planning_scheduler": {
                "displayName": "Print Planning Scheduler Plugin",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "Valemos",
                "repo": "OctoPrint-PrintPlanningScheduler",
                "current": self._plugin_version,
                # update method: pip
                "pip": "https://github.com/Valemos/OctoPrint-PrintPlanningScheduler/archive/{target_version}.zip",
            }
        }

    @octoprint.plugin.BlueprintPlugin.route("/upload_schedule", methods=["POST"])
    def upload_schedule(self):
        data = flask.request.get_json()
        if not data or "content" not in data:
            return flask.jsonify({"error": "No file content provided"}), 400

        file_content = data["content"]
        try:
            self._print_schedule.calendar = InfiniteCalendar.from_ical_str(file_content)
            self._save_schedule()
        except Exception as e:
            self._logger.exception(e)
            return (
                flask.jsonify(
                    {"message": f"ICal file cannot be parsed due to error: {e}"}
                ),
                422,
            )
        return flask.jsonify({"message": "Schedule updated successfully"}), 200

    def _date_or_default(self, date_str: str | None, default=None):
        if date_str is None:
            return default if default is not None else datetime.now()
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")

    def _parse_date_interval(self, start_date: str | None, end_date: str | None):
        if not start_date or not end_date:
            flask.abort(
                400,
                description="Cannot parse date interval start date and end date are required",
            )
        try:
            current_date = datetime.now()
            return DateInterval(
                self._date_or_default(start_date, current_date),
                self._date_or_default(end_date, current_date),
            )
        except Exception as e:
            flask.abort(Response({"message": f"Cannot parse date interval {e}"}, 400))

    @octoprint.plugin.BlueprintPlugin.route("/disabled_event", methods=["GET"])
    def get_disabled_events(self):
        target_interval = self._parse_date_interval(
            flask.request.args.get("start"), flask.request.args.get("end")
        )
        if target_interval.duration > timedelta(days=365):
            flask.abort(
                400,
                description="Target interval is over 365 days long. Please make it shorter",
            )
        intervals = self._print_schedule.calendar.get_intervals_as_events_for_period(
            target_interval
        )
        return flask.jsonify(intervals), 200

    @octoprint.plugin.BlueprintPlugin.route("/disabled_event", methods=["POST"])
    def add_disabled_event(self):
        data = flask.request.json
        event_name = data.get("event_name", None)
        target_interval = self._parse_date_interval(
            data.get("start", None), data.get("end", None)
        )
        rrule = data.get("rrule", None)
        self._print_schedule.calendar.add_event(
            target_interval.start, target_interval.end, event_name, rrule
        )
        self._save_schedule()
        return flask.jsonify({"message": "Event added successfully"}), 200

    @octoprint.plugin.BlueprintPlugin.route("/excluded_interval", methods=["GET"])
    def get_excluded_intervals(self):
        target_interval = self._parse_date_interval(
            flask.request.args.get("start"), flask.request.args.get("end")
        )
        interval_set = self._print_schedule.excluded_intervals.get_intervals_within(
            target_interval
        )
        return flask.jsonify(interval_set.intervals), 200

    @octoprint.plugin.BlueprintPlugin.route("/excluded_interval", methods=["POST"])
    def exclude_interval(self):
        target_interval = self._parse_date_interval(
            flask.request.args.get("start"), flask.request.args.get("end")
        )
        self._print_schedule.add_exclusion_interval(target_interval)
        self._save_schedule()
        return flask.jsonify({"message": "Interval excluded successfully"}), 200

    @octoprint.plugin.BlueprintPlugin.route("/print_job", methods=["GET"])
    def get_print_jobs(self):
        return flask.jsonify({"jobs": self._print_schedule.jobs}), 200

    @octoprint.plugin.BlueprintPlugin.route("/print_job", methods=["POST"])
    def add_print_job(self):
        data = flask.request.json
        name = data.get("name")
        duration = data.get("duration")
        description = data.get("description", "")
        if not name or not duration:
            flask.abort(400, description="Both name and duration are required")

        parsed_time = datetime.strptime(duration, "%H:%M")
        new_id = self._print_schedule.add_job(
            PrintJob(
                name,
                timedelta(hours=parsed_time.hour, minutes=parsed_time.minute),
                description,
            )
        )
        self._save_schedule()
        return (
            flask.jsonify(
                {"_id": new_id, "message": "Print job submitted successfully"}
            ),
            200,
        )

    @octoprint.plugin.BlueprintPlugin.route("/print_job", methods=["DELETE"])
    def remove_print_job(self):
        job_id = flask.request.args.get("job_id")
        if not job_id:
            flask.abort(400, description="job_id is required")

        removed_count = self._print_schedule.remove_job(job_id)
        self._save_schedule()
        return (
            flask.jsonify(
                {"message": "Print job remove success", "count": removed_count}
            ),
            200,
        )

    @octoprint.plugin.BlueprintPlugin.route("/suggested_print_jobs", methods=["GET"])
    def get_suggested_print_jobs(self):
        target_date = self._date_or_default(flask.request.args.get("date"))
        suggested_jobs = self._print_schedule.get_scheduled_job_options(target_date)
        return flask.jsonify(suggested_jobs), 200
