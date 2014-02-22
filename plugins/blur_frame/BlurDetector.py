from random import random
import os
from plugins.Plugin import Plugin

class BlurDetection(Plugin):
	"""Blur Plugin."""
	def __init__(self, config):
		self.config = config
		self.name = "BlurDetection"

	def process(self, frame):
		processResult = self.compute_FEAT_BLANKFRAME(frame)
		processDecision = False
		if processResult > self.config['threshold']:
			processDecision = True
		processDecision = True
		return processResult, processDecision


