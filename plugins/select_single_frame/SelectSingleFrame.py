from random import random
import os
from plugins.Plugin import Plugin

class SelectSingleFrame(Plugin):
	"""Plugin to let only 1 frame through."""
	def __init__(self, config):
		self.config = config
		self.name = "SelectSingleFrame"

	def process(self, frame):
		return 1, True

