# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
from octoprint.server.util.flask import restricted_access
from octoprint.server import admin_permission
import flask
from .flasher import MarlinFlasher
from .validation import RequestValidator
from .settings import SettingsWrapper
from .flasher.platform_type import PlatformType


class MarlinFlasherPlugin(octoprint.plugin.StartupPlugin,
						  octoprint.plugin.SettingsPlugin,
						  octoprint.plugin.AssetPlugin,
						  octoprint.plugin.TemplatePlugin,
						  octoprint.plugin.WizardPlugin,
						  octoprint.plugin.BlueprintPlugin):

	def on_after_startup(self):
		self.__flasher = MarlinFlasher(self.__settings_wrapper, self._printer, self, self._plugin_manager, self._identifier)
		self.__validator = RequestValidator(self.__settings_wrapper)

	def get_settings_defaults(self):
		return dict(
			arduino=dict(
				sketch_ino="Marlin.ino",
				cli_path=None,
				additional_urls=None
			),
			platformio=dict(

			),
			max_upload_size=20,
			platform_type=PlatformType.ARDUINO
		)

	def get_settings_version(self):
		return 1

	def on_settings_initialized(self):
		self.__settings_wrapper = SettingsWrapper(self._settings)

	def on_settings_migrate(self, target, current):
		if current is None:
			max_sketch_size = self._settings.get(["max_sketch_size"])
			self._settings.set(["max_upload_size"], max_sketch_size)
			self._settings.set(["max_sketch_size"], None)
			arduino_path = self._settings.get(["arduino_path"])
			self._settings.set(["arduino", "cli_path"], arduino_path)
			self._settings.set(["arduino_path"], None)
			sketch_ino = self._settings.get(["sketch_ino"])
			self._settings.set(["arduino", "sketch_ino"], sketch_ino)
			self._settings.set(["sketch_ino"], None)
			additional_urls = self._settings.get(["additional_urls"])
			self._settings.set(["additional_urls"], None)
			self._settings.set(["arduino", "additional_urls"], additional_urls)

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
		return 2

	def is_wizard_required(self):
		if self.__flasher.check_setup_errors():
			return True
		else:
			return False

	@octoprint.plugin.BlueprintPlugin.route("/upload_firmware", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def upload_firmware(self):
		errors = self.__validator.validate_upload()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.upload()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/cores/search", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def search_cores(self):
		errors = self.__validator.validate_core_search()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.core_search()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/libs/search", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def search_libs(self):
		errors = self.__validator.validate_lib_search()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.lib_search()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/cores/install", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def install_core(self):
		errors = self.__validator.validate_core_install()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.core_install()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/libs/install", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def install_lib(self):
		errors = self.__validator.validate_lib_install()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.lib_install()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/cores/uninstall", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def uninstall_core(self):
		errors = self.__validator.validate_core_uninstall()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.core_uninstall()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/libs/uninstall", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def uninstall_lib(self):
		errors = self.__validator.validate_lib_uninstall()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.lib_uninstall()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/board/listall", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def board_listall(self):
		errors = self.__validator.validate_board_listall()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.board_listall()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/board/details", methods=["GET"])
	@restricted_access
	@admin_permission.require(403)
	def board_detail(self):
		errors = self.__validator.validate_board_details()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.board_details()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

	@octoprint.plugin.BlueprintPlugin.route("/flash", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def flash(self):
		errors = self.__validator.validate_flash()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		result, errors = self.__flasher.flash()
		if errors:
			return flask.make_response(flask.jsonify(errors), 400)
		return flask.make_response(flask.jsonify(result), 200)

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
		return [("POST", r"/upload_firmware", self.__settings_wrapper.get_max_upload_size() * 1024 * 1024)]


__plugin_name__ = "Marlin Flasher"


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = MarlinFlasherPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.server.http.bodysize": __plugin_implementation__.body_size_hook
	}
