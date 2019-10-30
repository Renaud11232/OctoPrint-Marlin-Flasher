class BaseFlasher:

	def __init__(self, settings, printer):
		self._settings = settings
		self._printer = printer
		self._firmware = None
