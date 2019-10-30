from ..flasher.platform_type import PlatformType
from .platformio_validator import PlatformIOValidator
from .arduino_validator import ArduinoValidator
from .validator_error import ValidatorError


class RequestValidator:

	def __init__(self, settings, printer):
		self.__settings = settings
		self.__printer = printer
		self.__arduino_validator = ArduinoValidator(settings, printer)
		self.__platformio_validator = PlatformIOValidator(settings, printer)

	def __get_implementation(self):
		platform = self.__settings.get(["platform_type"])
		if platform == PlatformType.ARDUINO:
			return self.__arduino_validator
		elif platform == PlatformType.PLATFORM_IO:
			return self.__platformio_validator
		raise ValidatorError("Unknown firmware platform")
