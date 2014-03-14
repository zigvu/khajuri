from random import random
import os, Error
from plugins.blank_frame.BlankDetection import BlankDetection
from plugins.frame_extraction.FrameExtraction import FrameExtraction
from plugins.blur_frame.BlurDetection import BlurDetection
from plugins.select_single_frame.SelectSingleFrame import SelectSingleFrame
from plugins.model_eval.ModelDetectionHelper import ModelDetection

class PluginGroup:
	"""Container class representing a group of plugins that are
	evaluated with a FrameGroup in a DetectionStrand.

	Attributes:
		config	 					-- configuration file
	TODO:
		Use introspection to convert class string from config to plugin classes in init
	"""

	def __init__(self, config):
		self.pluginList = []
		self.filterMap = { "FrameExtraction" : FrameExtraction,
				   "BlankDetection" : BlankDetection,
				   "BlurDetection" : BlurDetection,
				   "SelectSingleFrame" : SelectSingleFrame }
		for plugin in config.getPluginClassNames():
			if not plugin.startswith( "Model" ):
				if self.filterMap.get( plugin ): 
					self.pluginList.append( self.filterMap[ plugin ]( config.getPluginConfig( plugin ) ) )
			else:
				modelConfig = config.getPluginConfig( plugin )
			    	self.pluginList.append(ModelDetection(modelConfig))

	def __iter__(self):
		"""Allow PluginGroup to behave like a regular list in for loops"""
		self.pluginListSize = len(self.pluginList)
		self.pluginListIndex = 0
		return self

	def next(self):
		"""Get next Plugin in iteration"""
		if self.pluginListIndex >= self.pluginListSize:
			raise StopIteration
		self.pluginListIndex += 1
		return self.pluginList[self.pluginListIndex - 1]

	def __str__(self):
		"""Return a nice string representation of the object."""
		return "Plugins: " + "; ".join(str(p) for p in self.pluginList)
