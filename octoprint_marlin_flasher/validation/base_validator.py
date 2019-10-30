from .validator_error import ValidatorError


class BaseValidator:

	def __init__(self, settings, printer):
		self._settings = settings
		self._printer = printer

	def validate_upload(self):
		raise ValidatorError("Unsupported function call.")

	def validate_core_search(self):
		raise ValidatorError("Unsupported function call.")

	def validate_lib_search(self):
		raise ValidatorError("Unsupported function call.")

	def validate_core_install(self):
		raise ValidatorError("Unsupported function call.")

	def validate_lib_install(self):
		raise ValidatorError("Unsupported function call.")

	def validate_core_uninstall(self):
		raise ValidatorError("Unsupported function call.")

	def validate_lib_uninstall(self):
		raise ValidatorError("Unsupported function call.")

	def validate_board_listall(self):
		raise ValidatorError("Unsupported function call.")

	def validate_board_details(self):
		raise ValidatorError("Unsupported function call.")

	def validate_flash(self):
		raise ValidatorError("Unsupported function call.")
