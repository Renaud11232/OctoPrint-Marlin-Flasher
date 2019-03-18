# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import flask
import zipfile
import shutil
import os


class MarlinFlasherPlugin(octoprint.plugin.SettingsPlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.TemplatePlugin,
							octoprint.plugin.WizardPlugin,
							octoprint.plugin.BlueprintPlugin):

	def get_settings_defaults(self):
		return dict(
			arduino_path=None,
			last_sketch=None,
			sketch_ino="Marlin.ino"
		)

	def get_assets(self):
		return dict(
			js=["js/marlin_flasher.js"],
			css=["css/marlin_flasher.css"]
		)

	@octoprint.plugin.BlueprintPlugin.route("/upload_sketch", methods=["POST"])
	def upload_sketch(self):
		upload_path = "sketch_file." + self._settings.global_get(["server", "uploads", "pathSuffix"])
		if upload_path not in flask.request.values:
			self._logger.warn("sketch_file was not included in the request")
			return flask.make_response("sketch_file not included", 400)
		path = flask.request.values[upload_path]
		with zipfile.ZipFile(path, "r") as zip:
			self._settings.set(["last_sketch"], None)
			shutil.rmtree(self.get_plugin_data_folder())
			zip.extractall(self.get_plugin_data_folder())
			for root, dirs, files in os.walk(self.get_plugin_data_folder()):
				for file in files:
					if file == self._settings.get(["sketch_ino"]):
						self._settings.set(["last_sketch"], root)
						return flask.make_response(root, 200)
		self._logger.warn("Unable to extract the given zip file")
		return flask.make_response("Unable to extract the given zip file", 500)

	def is_wizard_required(self):
		return self._settings.get(["arduino_path"]) is None

	def get_update_information(self):
		return dict(
			marlin_flasher=dict(
				displayName="Marlin Flasher",
				displayVersion=self._plugin_version,

				type="github_release",
				user="Renaud11232",
				repo="OctoPrint-Marlin-Flasher",
				current=self._plugin_version,

				pip="https://github.com/Renaud11232/OctoPrint-Marlin-Flasher/archive/{target_version}.zip"
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
