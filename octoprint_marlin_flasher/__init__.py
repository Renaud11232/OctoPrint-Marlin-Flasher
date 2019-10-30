# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
from octoprint.server.util.flask import restricted_access
from octoprint.server import admin_permission
import serial
import flask
import pyduinocli
import intelhex
from flask_babel import gettext
from .flasher import MarlinFlasher
from .validator import RequestValidator
import shlex
import zipfile
import shutil
import os
import re


class MarlinFlasherPlugin(octoprint.plugin.SettingsPlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.TemplatePlugin,
							octoprint.plugin.WizardPlugin,
							octoprint.plugin.BlueprintPlugin,
							octoprint.plugin.StartupPlugin):

	def on_after_startup(self):
		self.__sketch = None
		self.__sketch_ino = False
		self.__flasher = MarlinFlasher(self._settings, self._printer)
		self.__validator = RequestValidator(self._settings, self._printer)

	def get_settings_defaults(self):
		return dict(
			arduino_path=None,
			sketch_ino="Marlin.ino",
			max_sketch_size=20,
			additiona_urls=""
		)

	def get_assets(self):
		return dict(
			js=[
				"js/marlin_flasher.js"
			],
			css=[
				"css/marlin_flasher.css"
			]
		)

	def __handle_zip(self, zip_file):
		self.__sketch_ino = True
		extracted_dir = os.path.join(self.get_plugin_data_folder(), "extracted_sketch")
		sketch_dir = os.path.join(extracted_dir, os.path.splitext(self._settings.get(["sketch_ino"]))[0])
		if os.path.exists(extracted_dir):
			shutil.rmtree(extracted_dir)
		os.makedirs(sketch_dir)
		zip_file.extractall(sketch_dir)
		for root, dirs, files in os.walk(sketch_dir):
			for f in files:
				if f == self._settings.get(["sketch_ino"]):
					self.__sketch = root
					result = dict(
						path=root,
						file=f
					)
					return flask.make_response(flask.jsonify(result), 200)
		result = dict(message=gettext("No valid sketch found in the given file."))
		return flask.make_response(flask.jsonify(result), 400)

	def __handle_hex(self, path):
		self.__sketch_ino = False
		try:
			ih = intelhex.IntelHex()
			ih.loadhex(path)
		except intelhex.IntelHexError:
			result = dict(message=gettext("The given file is not a zip file nor a hex file"))
			return flask.make_response(flask.jsonify(result), 400)
		self.__sketch = os.path.join(self.get_plugin_data_folder(), "sketch.hex")
		shutil.copyfile(path, self.__sketch)
		result = dict(
			path=self.get_plugin_data_folder(),
			file="sketch.hex"
		)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/upload_sketch", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def upload_sketch(self):
		self.__sketch = None
		upload_path = "sketch_file." + self._settings.global_get(["server", "uploads", "pathSuffix"])
		if upload_path not in flask.request.values:
			result = dict(message=gettext("Missing sketch_file."))
			return flask.make_response(flask.jsonify(result), 400)
		path = flask.request.values[upload_path]
		try:
			with zipfile.ZipFile(path, "r") as zip_file:
				return self.__handle_zip(zip_file)
		except zipfile.BadZipfile:
			return self.__handle_hex(path)

	@octoprint.plugin.BlueprintPlugin.route("/cores/search", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def search_cores(self):
		if "query" not in flask.request.values:
			result = dict(message=gettext("Missing query."))
			return flask.make_response(flask.jsonify(result), 400)
		try:
			arduino = self.__get_arduino()
			arduino.core_update_index()
			result = arduino.core_search(self.__split(flask.request.values["query"]))
		except pyduinocli.ArduinoError as e:
			return flask.make_response(self.__get_error_json(e), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/libs/search", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def search_libs(self):
		if "query" not in flask.request.values:
			result = dict(message=gettext("Missing query."))
			return flask.make_response(flask.jsonify(result), 400)
		try:
			arduino = self.__get_arduino()
			arduino.lib_update_index()
			result = arduino.lib_search(self.__split(flask.request.values["query"]))
		except pyduinocli.ArduinoError as e:
			return flask.make_response(self.__get_error_json(e), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/cores/install", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def install_core(self):
		if "core" not in flask.request.values:
			result = dict(message=gettext("Missing core."))
			return flask.make_response(flask.jsonify(result), 400)
		try:
			arduino = self.__get_arduino()
			arduino.core_install([flask.request.values["core"]])
		except pyduinocli.ArduinoError as e:
			return flask.make_response(self.__get_error_json(e), 400)
		result = dict(core=flask.request.values["core"])
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/libs/install", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def install_lib(self):
		if "lib" not in flask.request.values:
			result = dict(message=gettext("Missing lib."))
			return flask.make_response(flask.jsonify(result), 400)
		try:
			arduino = self.__get_arduino()
			arduino.lib_install([flask.request.values["lib"]])
		except pyduinocli.ArduinoError as e:
			return flask.make_response(self.__get_error_json(e), 400)
		result = dict(lib=flask.request.values["lib"])
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/cores/uninstall", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def uninstall_core(self):
		if "core" not in flask.request.values:
			result = dict(message=gettext("Missing core."))
			return flask.make_response(flask.jsonify(result), 400)
		try:
			arduino = self.__get_arduino()
			arduino.core_uninstall([flask.request.values["core"]])
		except pyduinocli.ArduinoError as e:
			return flask.make_response(self.__get_error_json(e), 400)
		result = dict(core=flask.request.values["core"])
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/libs/uninstall", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def uninstall_lib(self):
		if "lib" not in flask.request.values:
			result = dict(message=gettext("Missing lib."))
			return flask.make_response(flask.jsonify(result), 400)
		try:
			arduino = self.__get_arduino()
			arduino.lib_uninstall([flask.request.values["lib"].replace(" ", "_")])
		except pyduinocli.ArduinoError as e:
			return flask.make_response(self.__get_error_json(e), 400)
		result = dict(lib=flask.request.values["lib"])
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/board/listall", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def board_listall(self):
		try:
			arduino = self.__get_arduino()
			arduino.core_update_index()
			result = arduino.board_listall()
			return flask.make_response(flask.jsonify(result), 200)
		except pyduinocli.ArduinoError as e:
			return flask.make_response(self.__get_error_json(e), 400)

	@octoprint.plugin.BlueprintPlugin.route("/board/details", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def board_detail(self):
		if "fqbn" not in flask.request.values or not flask.request.values["fqbn"]:
			result = dict(message=gettext("Missing fqbn."))
			return flask.make_response(flask.jsonify(result), 400)
		try:
			arduino = self.__get_arduino()
			result = arduino.board_details(flask.request.values["fqbn"])
			return flask.make_response(flask.jsonify(result), 200)
		except pyduinocli.ArduinoError as e:
			return flask.make_response(self.__get_error_json(e), 400)

	def __flash(self, fqbn):
		try:
			arduino = self.__get_arduino()
			if self.__sketch_ino:
				self._plugin_manager.send_plugin_message(self._identifier, dict(step=gettext("Compiling"), progress=0))
				arduino.compile(self.__sketch, fqbn=fqbn)
				self._plugin_manager.send_plugin_message(self._identifier, dict(step=gettext("Uploading"), progress=50))
			else:
				self._plugin_manager.send_plugin_message(self._identifier, dict(step=gettext("Uploading"), progress=0))
			transport = self._printer.get_transport()
			if not isinstance(transport, serial.Serial):
				result = dict(message=gettext("The printer is not connected through Serial."))
				return flask.make_response(result, 400)
			flash_port = transport.port
			_, port, baudrate, profile = self._printer.get_current_connection()
			self._printer.disconnect()
			if self.__sketch_ino:
				arduino.upload(sketch=self.__sketch, fqbn=fqbn, port=flash_port)
			else:
				arduino.upload(fqbn=fqbn, port=flash_port, input=self.__sketch)
			self._printer.connect(port, baudrate, profile)
			self.__sketch = None
			self._plugin_manager.send_plugin_message(self._identifier, dict(step=gettext("Done"), progress=100))
			result = dict(message=gettext("Board successfully flashed."))
			return flask.make_response(flask.jsonify(result), 200)
		except pyduinocli.ArduinoError as e:
			return flask.make_response(self.__get_error_json(e), 400)

	@octoprint.plugin.BlueprintPlugin.route("/flash", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def flash(self):
		if "fqbn" not in flask.request.values or not flask.request.values["fqbn"]:
			result = dict(message=gettext("Missing fqbn."))
			return flask.make_response(flask.jsonify(result), 400)
		if self.__sketch is None:
			result = dict(message=gettext("No sketch uploaded."))
			return flask.make_response(flask.jsonify(result), 400)
		if not self._printer.is_ready():
			result = dict(message=gettext("The printer is currently not ready. Is it connected/idle ?"))
			return flask.make_response(flask.jsonify(result), 409)
		options = []
		for param in flask.request.values:
			if param != "fqbn":
				options.append("%s=%s" % (param, flask.request.values[param]))
		options = ",".join(options)
		fqbn = flask.request.values["fqbn"]
		if options:
			fqbn = "%s:%s" % (fqbn, options)
		return self.__flash(fqbn)

	@staticmethod
	def __split(string):
		s = shlex.split(string)
		if len(s) == 0:
			return [""]
		return s

	def __get_arduino(self):
		arduino_path = self._settings.get(["arduino_path"])
		additional_urls = self._settings.get(["additional_urls"])
		if additional_urls:
			additional_urls = additional_urls.splitlines()
		else:
			additional_urls = None
		return pyduinocli.Arduino(arduino_path, additional_urls=additional_urls)

	@staticmethod
	def __get_error_json(error):
		return flask.jsonify(dict(
			message=error.message,
			cause=error.cause,
			stderr=error.stderr
		))

	def get_wizard_version(self):
		return 2

	def is_wizard_required(self):
		no_arduino_path = self._settings.get(["arduino_path"]) is None
		bad_arduino = False
		if not no_arduino_path:
			try:
				bad_arduino = re.match(r"(?:0\.5\..+?)\Z", self.__get_arduino().version()["VersionString"]) is None
			except (pyduinocli.ArduinoError, KeyError):
				bad_arduino = True
		return no_arduino_path or bad_arduino

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

	def body_size_hook(self, current_max_body_sizes, *args, **kwargs):
		return [("POST", r"/upload_sketch", self._settings.get_int(["max_sketch_size"]) * 1024 * 1024)]


__plugin_name__ = "Marlin Flasher"


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = MarlinFlasherPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.server.http.bodysize": __plugin_implementation__.body_size_hook
	}
