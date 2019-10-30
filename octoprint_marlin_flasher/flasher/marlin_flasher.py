from .flasher_error import FlasherError
from .arduino_flasher import ArduinoFlasher
from .platformio_flasher import PlatformIOFlasher
from .platform_type import PlatformType


class MarlinFlasher:

	def __init__(self, settings, printer):
		self.__firmware = None
		self.__settings = settings
		self.__arduino_flasher = ArduinoFlasher(settings, printer)
		self.__platformio_flasher = PlatformIOFlasher(settings, printer)

	def __get_implementation(self):
		platform = self.__settings.get(["platform_type"])
		if platform == PlatformType.ARDUINO:
			return self.__arduino_flasher
		elif platform == PlatformType.PLATFORM_IO:
			return self.__platformio_flasher
		raise FlasherError("Unknown firmware platform")
