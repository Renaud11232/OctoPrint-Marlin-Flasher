# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
from octoprint.server.util.flask import restricted_access
from octoprint.server import admin_permission
from octoprint.events import Events
import flask
from .flasher import PlatformIOFlasher, ArduinoFlasher
from .flasher.retrieving_method import RetrievingMethod
from .validation import ArduinoValidator, PlatformIOValidator
from .settings import SettingsWrapper
from .flasher.platform_type import PlatformType


class MarlinFlasherPlugin(octoprint.plugin.SettingsPlugin,
						  octoprint.plugin.AssetPlugin,
						  octoprint.plugin.TemplatePlugin,
						  octoprint.plugin.WizardPlugin,
						  octoprint.plugin.BlueprintPlugin,
						  octoprint.plugin.EventHandlerPlugin):

	def initialize(self):
		self.__settings_wrapper = SettingsWrapper(self._settings)
		self.__arduino = ArduinoFlasher(self.__settings_wrapper, self._printer, self, self._plugin_manager, self._identifier, self._logger)
		self.__platformio = PlatformIOFlasher(self.__settings_wrapper, self._printer, self, self._plugin_manager, self._identifier, self._logger)
		self.__arduino_validator = ArduinoValidator(self.__settings_wrapper)
		self.__platformio_validator = PlatformIOValidator(self.__settings_wrapper)

	def get_settings_defaults(self):
		return dict(
			arduino=dict(
				sketch_ino="Marlin.ino",
				cli_path=None,
				additional_urls=None,
				last_flash_options=None
			),
			platformio=dict(
				cli_path=None,
				last_flash_options=None
			),
			max_upload_size=20,
			platform_type=PlatformType.ARDUINO,
			pre_flash_script=None,
			pre_flash_delay=0,
			post_flash_script=None,
			post_flash_delay=0,
			retrieving_method=RetrievingMethod.UPLOAD
		)

	def get_settings_version(self):
		return 1

	def on_settings_migrate(self, target, current):
		defaults = self.get_settings_defaults()
		if current is None or current < 1:
			max_sketch_size = self._settings.get(["max_sketch_size"])
			if max_sketch_size is None:
				max_sketch_size = defaults["max_upload_size"]
			self._settings.set(["max_upload_size"], max_sketch_size)
			self._settings.set(["max_sketch_size"], None)
			arduino_path = self._settings.get(["arduino_path"])
			self._settings.set(["arduino", "cli_path"], arduino_path)
			self._settings.set(["arduino_path"], None)
			sketch_ino = self._settings.get(["sketch_ino"])
			if sketch_ino is None:
				sketch_ino = defaults["arduino"]["sketch_ino"]
			self._settings.set(["arduino", "sketch_ino"], sketch_ino)
			self._settings.set(["sketch_ino"], None)
			additional_urls = self._settings.get(["additional_urls"])
			self._settings.set(["additional_urls"], None)
			self._settings.set(["arduino", "additional_urls"], additional_urls)

	def on_settings_save(self, data):
		if "platform_type" in data:
			platform = data["platform_type"]
			if platform == PlatformType.ARDUINO:
				flasher = self.__arduino
			else:
				flasher = self.__platformio
			flasher.send_initial_state()
		return super(MarlinFlasherPlugin, self).on_settings_save(data)

	def get_assets(self):
		return dict(
			js=[
				"js/marlin_flasher.js"
			],
			css=[
				"css/marlin_flasher.css"
			]
		)

	def get_wizard_version(self):
		return 4

	def is_wizard_required(self):
		return True

	def on_event(self, event, payload):
		platform = self.__settings_wrapper.get_platform_type()
		if platform == PlatformType.ARDUINO:
			flasher = self.__arduino
		else:
			flasher = self.__platformio
		if event == Events.CONNECTED:
			self._logger.debug("Intercepted CONNECTED event")
			flasher.handle_connected_event()
		elif event == Events.USER_LOGGED_IN:
			self._logger.debug("Intercepted USER_LOGGED_IN event")
			flasher.send_initial_state()

	def __handle_unvalidated_request(self, handler):
		result, errors = handler()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	def __handle_validated_request(self, validator, handler, setup_checker):
		setup_errors = setup_checker()
		if setup_errors:
			return flask.make_response(flask.jsonify(setup_errors), 400)
		errors = validator()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return self.__handle_unvalidated_request(handler)

	####################################################################
	# Arduino
	####################################################################

	@octoprint.plugin.BlueprintPlugin.route("/arduino/install", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def arduino_install(self):
		return self.__handle_unvalidated_request(self.__arduino.start_install)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/upload_firmware", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def upload_arduino_firmware(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_upload, self.__arduino.upload, self.__arduino.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/download_firmware", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def download_arduino_firmware(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_download, self.__arduino.download, self.__arduino.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/cores/search", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def search_arduino_cores(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_core_search, self.__arduino.core_search, self.__arduino.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/cores/install", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def install_arduino_core(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_core_install, self.__arduino.core_install, self.__arduino.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/cores/uninstall", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def uninstall_arduino_core(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_core_uninstall, self.__arduino.core_uninstall, self.__arduino.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/libs/search", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def search_arduino_libs(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_lib_search, self.__arduino.lib_search, self.__arduino.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/libs/install", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def install_arduino_lib(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_lib_install, self.__arduino.lib_install, self.__arduino.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/libs/uninstall", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def uninstall_arduino_lib(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_lib_uninstall, self.__arduino.lib_uninstall, self.__arduino.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/board/details", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def board_detail(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_board_details, self.__arduino.board_details, self.__arduino.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/arduino/flash", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def arduino_flash(self):
		return self.__handle_validated_request(self.__arduino_validator.validate_flash, self.__arduino.flash, self.__arduino.check_setup_errors)

	####################################################################
	# PlatformIO
	####################################################################

	@octoprint.plugin.BlueprintPlugin.route("/platformio/install", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def platformio_install(self):
		return self.__handle_unvalidated_request(self.__platformio.start_install)

	@octoprint.plugin.BlueprintPlugin.route("/platformio/upload_firmware", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def upload_platformio_firmware(self):
		return self.__handle_validated_request(self.__platformio_validator.validate_upload, self.__platformio.upload, self.__platformio.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/platformio/download_firmware", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def download_platoformio_firmware(self):
		return self.__handle_validated_request(self.__platformio_validator.validate_download, self.__platformio.download, self.__platformio.check_setup_errors)

	@octoprint.plugin.BlueprintPlugin.route("/platformio/flash", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def platformio_flash(self):
		return self.__handle_validated_request(self.__platformio_validator.validate_flash, self.__platformio.flash, self.__platformio.check_setup_errors)

	def get_update_information(self):
		return dict(
			marlin_flasher=dict(
				displayName="Marlin Flasher",
				displayVersion=self._plugin_version,

				type="github_release",
				user="Renaud11232",
				repo="OctoPrint-Marlin-Flasher",
				current=self._plugin_version,

				pip="https://github.com/Renaud11232/OctoPrint-Marlin-Flasher/archive/{target_version}.zip",

				stable_branch=dict(
					name="Stable",
					branch="master"
				),

				prerelease_branches=[
					dict(
						name="Prerelease",
						branch="prerelease"
					)
				]
			)
		)

	def body_size_hook(self, current_max_body_sizes, *args, **kwargs):
		return [
			("POST", r"/arduino/upload_firmware", self.__settings_wrapper.get_max_upload_size() * 1024 * 1024),
			("POST", r"/platformio/upload_firmware", self.__settings_wrapper.get_max_upload_size() * 1024 * 1024)
		]

	def additional_excludes_hook(self, excludes, *args, **kwargs):
		return ["arduino-cli", "platformio", "firmware_arduino", "firmware_platformio"]


__plugin_name__ = "Marlin Flasher"
__plugin_pythoncompat__ = ">=2.7,<4"


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = MarlinFlasherPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.server.http.bodysize": __plugin_implementation__.body_size_hook,
		"octoprint.plugin.backup.additional_excludes": __plugin_implementation__.additional_excludes_hook
	}
