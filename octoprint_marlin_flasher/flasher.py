from .platform_type import PlatformType
from .flasher_error import FlasherError
from .arduino_flasher import ArduinoFlasher
from .platformio_flasher import PlatformIOFlasher


class BaseFlasher:

	def __init__(self, settings, printer):
		self._settings = settings
		self._printer = printer

	def handle_upload(self):
		pass

	def flash(self):
		raise FlasherError("Unsupported function call.")

	def compile(self):
		raise FlasherError("Unsupported function call.")


class MarlinFlasher(BaseFlasher):

	def __init__(self, settings, printer):
		BaseFlasher.__init__(self, settings, printer)
		self.__arduino = ArduinoFlasher(settings, printer)
		self.__platformio = PlatformIOFlasher(settings, printer)

	def __get_implementation(self):
		platform = self._settings.get(["platform_type"])
		if platform == PlatformType.ARDUINO:
			return self.__arduino
		elif platform == PlatformType.PLATFORM_IO:
			return self.__platformio
		raise FlasherError("Unknown firmware platform")

	def flash(self):
		return self.__get_implementation().flash()

	def compile(self):
		return self.__get_implementation().compile()
