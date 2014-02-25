from random import random
class Plugin:
	"""Base class for all plugins.
	All common computaion is written here - such computation methods
	are named compute_* with * representing the feature to be computed.
	"""
	def __init__(self):
		pass

	def __str__(self):
		"""Return a nice string representation of the object."""
		return self.name

	def compute_FEAT_BLANKFRAME(self, frame):
		return random()
		# if frame.FEAT_BLANKFRAME == None:
		# 	frame.FEAT_BLANKFRAME = 1
		# 	print "In Plugin setting value"

class VisionDetection(Plugin):
	"""Base class for all vision detection."""
	def __init__(self, config):
		self.config = config

	def process(self, frame):
		processResult = 0.5 - random()
		processDecision = False
		if processResult > 0:
			processDecision = True
		return processResult, processDecision
