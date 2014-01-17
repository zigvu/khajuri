""" Class describing all errors."""

class Error(Exception):
	"""Base class for all errors in khajuri"""
	pass

# --------------------------------------------------------
# Frame Errors

class FrameError(Error):
	"""Base class for all frame related errors
	Attributes:
		frameNumber	-- frame number whose access caused to raise this error
		message 		-- text message explaning the cause of this error
	"""
	def __init__(self, frameNumber, message):
		self.frameNumber = frameNumber
		self.message = message

	def __str__(self):
		"""Return a nice string representation of the object."""
		return str(self.message) + "; Frame " + str(self.frameNumber)

class FrameOutOfBoundsError(FrameError):
	"""Error in trying to access frames not in video"""

	def __init__(self, frameNumber, message):
		FrameError(frameNumber, message)


# --------------------------------------------------------
# Result Errors

class ResultError(Error):
	"""Base class for all result related errors
	Attributes:
		frame				-- frame for which this error was raised
		plugin			-- plugin for which this error was raised
		message 		-- text message explaning the cause of this error
	"""
	def __init__(self, frame, plugin, message):
		self.frame = frame
		self.plugin = plugin
		self.message = message

	def __str__(self):
		"""Return a nice string representation of the object."""
		return str(self.message) + "; " + str(self.frame) + str(self.plugin)


class ResultIncorrectStateError(ResultError):
	"""Result in incorrect state for evaluation"""

	def __init__(self, frame, plugin, message):
		ResultError(frame, plugin, message)


class ResultNotFoundError(ResultError):
	"""Result not found in result list"""

	def __init__(self, frame, plugin, message):
		ResultError(frame, plugin, message)


# --------------------------------------------------------
# Plugin Errors

class PluginError(Error):
	"""Base class for all plugin related errors
	Attributes:
		plugin			-- plugin for which this error was raised
		message 		-- text message explaning the cause of this error
	"""
	def __init__(self, plugin, message):
		self.plugin = plugin
		self.message = message

	def __str__(self):
		"""Return a nice string representation of the object."""
		return str(self.message) + "; " + str(self.plugin)


class PluginNonExistError(PluginError):
	"""Plugin doesn't exist"""

	def __init__(self, pluginClassName, message):
		# note: can't pass to Super since Super only takes plugin 
		self.pluginClassName = pluginClassName
		self.message = message

	def __str__(self):
		"""Return a nice string representation of the object."""
		return str(self.message) + "; " + str(self.pluginClassName)
