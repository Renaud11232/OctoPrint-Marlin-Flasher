# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import flask
import pyduinocli
import zipfile
import shutil
import os


# TODO refactor & cleanup + placeholders + check punctuation
class MarlinFlasherPlugin(octoprint.plugin.SettingsPlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.TemplatePlugin,
							octoprint.plugin.WizardPlugin,
							octoprint.plugin.BlueprintPlugin,
							octoprint.plugin.StartupPlugin):

	def on_after_startup(self):
		self.__sketch = None

	def get_settings_defaults(self):
		return dict(
			arduino_path=None,
			sketch_ino="Marlin.ino"
		)

	def get_assets(self):
		return dict(
			js=[
				"js/bootstrap-table.js",
				"js/marlin_flasher.js"
			],
			css=[
				"css/bootstrap-table.css",
				"css/marlin_flasher.css"
			]
		)

	@octoprint.plugin.BlueprintPlugin.route("/upload_sketch", methods=["POST"])
	def upload_sketch(self):
		upload_path = "sketch_file." + self._settings.global_get(["server", "uploads", "pathSuffix"])
		if upload_path not in flask.request.values:
			result = dict(
				error="Missing sketch_file"
			)
			return flask.make_response(flask.jsonify(result), 400)
		path = flask.request.values[upload_path]
		try:
			with zipfile.ZipFile(path, "r") as zip_file:
				self.__sketch = None
				sketch_dir = os.path.join(self.get_plugin_data_folder(), "extracted_sketch")
				if os.path.exists(sketch_dir):
					shutil.rmtree(sketch_dir)
				os.makedirs(sketch_dir)
				zip_file.extractall(sketch_dir)
				for root, dirs, files in os.walk(sketch_dir):
					for f in files:
						if f == self._settings.get(["sketch_ino"]):
							self.__sketch = root
							result = dict(
								path=root,
								ino=f
							)
							return flask.make_response(flask.jsonify(result), 200)
				shutil.rmtree(sketch_dir)
				result = dict(
					error="No valid sketch found in the given file"
				)
				return flask.make_response(flask.jsonify(result), 400)
		except zipfile.BadZipfile:
			result = dict(
				error="The given file was not a zip file"
			)
			return flask.make_response(flask.jsonify(result), 400)

	@octoprint.plugin.BlueprintPlugin.route("/cores/search", methods=["GET"])
	def search_cores(self):
		if "query" not in flask.request.values:
			result = dict(
				error="Missing query"
			)
			return flask.make_response(flask.jsonify(result), 400)
		arduino = self.__get_arduino()
		try:
			arduino.core_update_index()
			search_result = arduino.core_search(*flask.request.values["query"].split(" "))
		except pyduinocli.ArduinoError as e:
			result = dict(
				error=e.error_info["Message"]
			)
			return flask.make_response(flask.jsonify(result), 400)
		if "Platforms" not in search_result:
			search_result = dict(
				Platforms=[]
			)
		return flask.make_response(flask.jsonify(search_result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/libs/search", methods=["GET"])
	def search_libs(self):
		if "query" not in flask.request.values:
			result = dict(
				error="Missing query"
			)
			return flask.make_response(flask.jsonify(result), 400)
		arduino = self.__get_arduino()
		try:
			arduino.lib_update_index()
			search_result = arduino.lib_search(*flask.request.values["query"].split(" "))
		except pyduinocli.ArduinoError as e:
			result = dict(
				error=e.error_info["Message"]
			)
			return flask.make_response(flask.jsonify(result), 400)
		if "libraries" not in search_result:
			search_result = dict(
				libraries=[]
			)
		return flask.make_response(flask.jsonify(search_result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/cores/install", methods=["POST"])
	def install_core(self):
		if "core" not in flask.request.values:
			result = dict(
				error="Missing core"
			)
			return flask.make_response(flask.jsonify(result), 400)
		arduino = self.__get_arduino()
		try:
			arduino.core_install(flask.request.values["core"])
		except pyduinocli.ArduinoError as e:
			result = dict(
				error=e.error_info["Message"]
			)
			return flask.make_response(flask.jsonify(result), 400)
		result = dict(
			core=flask.request.values["core"]
		)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/libs/install", methods=["POST"])
	def install_lib(self):
		if "lib" not in flask.request.values:
			result = dict(
				error="Missing lib"
			)
			return flask.make_response(flask.jsonify(result), 400)
		arduino = self.__get_arduino()
		try:
			arduino.lib_install(flask.request.values["lib"])
		except pyduinocli.ArduinoError as e:
			result = dict(
				error=e.error_info["Message"]
			)
			return flask.make_response(flask.jsonify(result), 400)
		result = dict(
			lib=flask.request.values["lib"]
		)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/cores/uninstall", methods=["POST"])
	def uninstall_core(self):
		if "core" not in flask.request.values:
			result = dict(
				error="Missing core"
			)
			return flask.make_response(flask.jsonify(result), 400)
		arduino = self.__get_arduino()
		try:
			arduino.core_uninstall(flask.request.values["core"])
		except pyduinocli.ArduinoError as e:
			result = dict(
				error=e.error_info["Message"]
			)
			return flask.make_response(flask.jsonify(result), 400)
		result = dict(
			core=flask.request.values["core"]
		)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/libs/uninstall", methods=["POST"])
	def uninstall_lib(self):
		if "lib" not in flask.request.values:
			result = dict(
				error="Missing lib"
			)
			return flask.make_response(flask.jsonify(result), 400)
		arduino = self.__get_arduino()
		try:
			arduino.lib_uninstall(flask.request.values["lib"])
		except pyduinocli.ArduinoError as e:
			result = dict(
				error=e.error_info["Message"]
			)
			return flask.make_response(flask.jsonify(result), 400)
		result = dict(
			core=flask.request.values["lib"]
		)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/board/listall", methods=["GET"])
	def board_listall(self):
		arduino = self.__get_arduino()
		try:
			result = arduino.board_listall()
			return flask.make_response(flask.jsonify(result), 200)
		except pyduinocli.ArduinoError as e:
			result = dict(
				error=e.error_info["Message"]
			)
			return flask.make_response(flask.jsonify(result), 400)

	@octoprint.plugin.BlueprintPlugin.route("/flash", methods=["POST"])
	def flash(self):
		if "board" not in flask.request.values or not flask.request.values["board"]:
			result = dict(
				error="Missing board"
			)
			return flask.make_response(flask.jsonify(result), 400)
		fqbn = flask.request.values["board"]
		if self.__sketch is None:
			result = dict(
				error="No sketch uploaded"
			)
			return flask.make_response(flask.jsonify(result), 400)
		if not self._printer.is_ready():
			result = dict(
				error="The printer is currently not ready"
			)
			return flask.make_response(flask.jsonify(result), 409)
		connection_string, port, baudrate, profile = self._printer.get_current_connection()
		self._printer.disconnect()
		arduino = self.__get_arduino()
		try:
			arduino.compile(self.__sketch, fqbn=fqbn)
			arduino.upload(self.__sketch, fqbn=fqbn, port=port)
			self._printer.connect(port, baudrate, profile)
			result = dict(
				message="Board successfully flashed"
			)
			return flask.make_response(flask.jsonify(result), 200)
		except pyduinocli.ArduinoError as e:
			result = dict(
				error=e.error_info["Message"]
			)
			return flask.make_response(flask.jsonify(result), 400)

	def __get_arduino(self):
		arduino_path = self._settings.get(["arduino_path"])
		return pyduinocli.Arduino(arduino_path)

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
