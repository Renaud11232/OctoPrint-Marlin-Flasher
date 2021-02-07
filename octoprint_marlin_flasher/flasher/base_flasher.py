from .flasher_error import FlasherError
import time
import flask
import requests
import tempfile
import os


class BaseFlasher:

	def __init__(self, settings, printer, plugin, plugin_manager, identifier):
		self._settings = settings
		self._printer = printer
		self._plugin = plugin
		self._plugin_manager = plugin_manager
		self._identifier = identifier
		self._firmware = None
		self._firmware_version = None
		self._firmware_author = None
		self._firmware_upload_time = None
		self._should_run_post_script = False

	def _run_pre_flash_script(self):
		pre_flash_script = self._settings.get_pre_flash_script()
		if pre_flash_script:
			commands = [line.strip() for line in pre_flash_script.splitlines()]
			self._printer.commands(commands)

	def _wait_pre_flash_delay(self):
		time.sleep(self._settings.get_pre_flash_delay())

	def _run_post_flash_script(self):
		post_flash_script = self._settings.get_post_flash_script()
		if post_flash_script:
			commands = [line.strip() for line in post_flash_script.splitlines()]
			self._printer.commands(commands)

	def _wait_post_flash_delay(self):
		time.sleep(self._settings.get_post_flash_delay())

	def _validate_firmware_file(self, file_path):
		raise FlasherError("Unsupported function call.")

	def handle_connected_event(self):
		if self._should_run_post_script:
			self._run_post_flash_script()
			self._should_run_post_script = False

	def check_setup_errors(self):
		raise FlasherError("Unsupported function call.")

	def upload(self):
		uploaded_file_path = flask.request.values["firmware_file." + self._settings.get_upload_path_suffix()]
		errors = self._validate_firmware_file(uploaded_file_path)
		if errors:
			return None, errors
		return self._handle_firmware_file(uploaded_file_path)

	def download(self):
		r = requests.get(flask.request.values["url"])
		with tempfile.NamedTemporaryFile(delete=False) as temp:
			temp.write(r.content)
			temp_path = temp.name
		errors = self._validate_firmware_file(temp_path)
		if errors:
			os.remove(temp_path)
			return None, errors
		result = self._handle_firmware_file(temp_path)
		os.remove(temp_path)
		return result

	def _handle_firmware_file(self, firmware_file_path):
		raise FlasherError("Unsupported function call.")

	def firmware(self):
		raise FlasherError("Unsupported function call.")

	def core_search(self):
		raise FlasherError("Unsupported function call.")

	def lib_search(self):
		raise FlasherError("Unsupported function call.")

	def core_install(self):
		raise FlasherError("Unsupported function call.")

	def lib_install(self):
		raise FlasherError("Unsupported function call.")

	def core_uninstall(self):
		raise FlasherError("Unsupported function call.")

	def lib_uninstall(self):
		raise FlasherError("Unsupported function call.")

	def board_listall(self):
		raise FlasherError("Unsupported function call.")

	def board_details(self):
		raise FlasherError("Unsupported function call.")

	def flash(self):
		raise FlasherError("Unsupported function call.")

	def last_flash_options(self):
		raise FlasherError("Unsupported function call.")
