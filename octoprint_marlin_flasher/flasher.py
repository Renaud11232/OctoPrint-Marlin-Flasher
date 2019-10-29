from .platform_type import PlatformType
from .flasher_error import FlasherError
from .arduino_flasher import ArduinoFlasher
from .platformio_flasher import PlatformIOFlasher


class BaseFlasher:

	def __init__(self, settings, printer):
		self._settings = settings
		self._printer = printer
		self._firmware = None

	def handle_upload(self):
		raise FlasherError("Unsupported function call.")

	def flash(self):
		raise FlasherError("Unsupported function call.")

	def compile(self):
		raise FlasherError("Unsupported function call.")


class MarlinFlasher(ArduinoFlasher, PlatformIOFlasher):

	def __init__(self, settings, printer):
		ArduinoFlasher.__init__(self, settings, printer)
		PlatformIOFlasher.__init__(self, settings, printer)

	def __get_implementation(self):
		platform = self._settings.get(["platform_type"])
		if platform == PlatformType.ARDUINO:
			return ArduinoFlasher
		elif platform == PlatformType.PLATFORM_IO:
			return PlatformIOFlasher
		raise FlasherError("Unknown firmware platform")

	def handle_upload(self):
		return self.__get_implementation().handle_upload(self)

	def flash(self):
		return self.__get_implementation().flash(self)

	def compile(self):
		return self.__get_implementation().compile(self)
