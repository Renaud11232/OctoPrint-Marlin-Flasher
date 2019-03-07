# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin

class MarlinFlasherPlugin(octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.AssetPlugin,
                           octoprint.plugin.TemplatePlugin):

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			# put your plugin's default settings here
		)

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/marlin_flasher.js"],
			css=["css/marlin_flasher.css"],
			less=["less/marlin_flasher.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			marlin_flasher=dict(
				displayName="Marlin_flasher Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="you",
				repo="OctoPrint-Marlin-Flasher",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/you/OctoPrint-Marlin-Flasher/archive/{target_version}.zip"
			)
		)


__plugin_name__ = "Marlin Flasher"


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = MarlinFlasherPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

