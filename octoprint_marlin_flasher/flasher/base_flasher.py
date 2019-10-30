from .flasher_error import FlasherError


class BaseFlasher:

	def __init__(self, settings, printer):
		self._settings = settings
		self._printer = printer
		self._firmware = None

	def check_setup_errors(self):
		raise FlasherError("Unsupported function call.")

	def upload_file(self):
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

	def compile(self):
		raise FlasherError("Unsupported function call.")

	def upload(self):
		raise FlasherError("Unsupported function call.")
