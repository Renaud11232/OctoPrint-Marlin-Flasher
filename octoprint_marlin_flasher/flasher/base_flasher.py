from .flasher_error import FlasherError


class BaseFlasher:

	def __init__(self, settings, printer):
		self._settings = settings
		self._printer = printer
		self._firmware = None

	def handle_upload(self):
		raise FlasherError("Unsupported function call.")

	def flash(self, firmware):
		raise FlasherError("Unsupported function call.")

	def compile(self, firmware):
		raise FlasherError("Unsupported function call.")
