from .flasher_error import FlasherError


class BaseFlasher:

	def __init__(self, settings, printer, plugin, plugin_manager, identifier):
		self._settings = settings
		self._printer = printer
		self._plugin = plugin
		self._plugin_manager = plugin_manager
		self._identifier = identifier
		self._firmware = None
		self._firmware_upload_time = None
		self._shoud_run_post_script = False

	def _run_pre_flash_script(self):
		pre_flash_script = self._settings.get_pre_flash_script()
		if pre_flash_script:
			commands = [line.strip() for line in pre_flash_script.split(r"\n")]
			self._printer.commands(commands)

	def _run_post_flash_script(self):
		post_flash_script = self._settings.get_post_flash_script()
		if post_flash_script:
			commands = [line.strip() for line in post_flash_script.split(r"\n")]
			self._printer.commands(commands)

	def handle_connected_event(self):
		if self._shoud_run_post_script:
			self._run_post_flash_script()
			self._shoud_run_post_script = False

	def check_setup_errors(self):
		raise FlasherError("Unsupported function call.")

	def upload(self):
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
