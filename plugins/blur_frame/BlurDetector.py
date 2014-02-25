import os
from plugins.Plugin import Plugin

class BlurDetection(Plugin):
	"""Blur Plugin."""
	def __init__(self, config):
		self.config = config
		self.name = "BlurDetection"

	def process(self, frame):
	        # Use Value from Blank Detection in Blur
		if hasattr(frame.vFrame, 'Is_Blank'):
	        	print frame.vFrame.Is_Blank
		else:
			print 'Blank Computation is not done yet'
		processResult = self.compute_FEAT_BLANKFRAME(frame)
		processDecision = False
		if processResult > self.config['threshold']:
			processDecision = True
		processDecision = True
		return processResult, processDecision


