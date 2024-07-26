import octoprint.plugin


class PrintPlanningSchedulerPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
):

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
            "js": ["js/print_planning_scheduler.js"],
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
