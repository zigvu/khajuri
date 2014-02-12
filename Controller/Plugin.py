""" Class describing all plugins."""

# TODO: Remove
from random import random
import ModelDetectionHelper
import BlankImageDetection
import os, Error

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
		# set default plugins
		# for pl in GLOBAL_ALL_PLUGINS:
		# 	self.pluginList.append(pl)
		self.pluginList.append(FrameExtraction(config))
		self.pluginList.append(BlankDetection(config.getPluginConfig('BlankDetection')))
		#self.pluginList.append(BlurDetection(config.getPluginConfig('BlurDetection')))
		self.pluginList.append(SelectSingleFrame(config.getPluginConfig('SelectSingleFrame')))
		self.pluginList.append(RemoveMultiModels(config.getPluginConfig('RemoveMultiModels')))
		for i in xrange( 1000 ):
			try:
				modelConfig = config.getPluginConfig('ModelDetection%s' % i)
			    	self.pluginList.append(ModelDetection(modelConfig))
			except Error.PluginNonExistError:
				break

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


# TODO: Move off file:

class FrameExtraction(Plugin):
	"""Frame Extraction Plugin."""
	def __init__(self, config):
		self.name = "FrameExtraction"
		self.config = config
		self.videoFrameReader = self.config.videoFrameReader

	def process(self, frame):
	        frame.vFrame = self.videoFrameReader.getFrameWithFrameNumber( int( frame.frameNumber ) )
		while not frame.vFrame:
	        	frame.vFrame = self.videoFrameReader.getFrameWithFrameNumber( int( frame.frameNumber ) )
		frameDir = os.path.join( self.config.baseFrameFolder, str( frame.frameNumber ) )
		if not os.path.exists( frameDir ):
			os.makedirs( frameDir )
		frame.imgName = os.path.join( frameDir, "original.ppm" )
                self.videoFrameReader.saveFrameWithFrameNumber( int( frame.frameNumber ), frame.imgName )
		return 1, True

class BlankDetection(Plugin):
	"""Blank Plugin."""
	def __init__(self, config):
		self.config = config
		self.name = "BlankDetection"

	def process(self, frame):
                result = BlankImageDetection.Is_Blank( frame.imgName )
		processDecision = False
		if result[0] == 0:
			processDecision = True
		return result[1], processDecision


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
		return processResult, processDecision


class SelectSingleFrame(Plugin):
	"""Plugin to let only 1 frame through."""
	def __init__(self, config):
		self.config = config
		self.name = "SelectSingleFrame"

	def process(self, frame):
		return 1, True

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

class RemoveMultiModels(VisionDetection):
	"""Model Detection Plugin."""
	def __init__(self, config):
		VisionDetection.__init__(self, config)
		self.name = "RemoveMultiModels"

modelDetectionHelpers = {}
class ModelDetection(VisionDetection):
	"""Model Detection Plugin."""
	def __init__(self, config):
		VisionDetection.__init__(self, config)
		self.modelName = config[ 'modelName' ]
		self.modelVersion = config[ 'modelVersion' ]
		self.name = "%s:%s:%s" % ( "ModelDetection", self.modelName, self.modelVersion )
		self.modelDir = "structSVM-data/datasets/%s.%s/models/" % ( self.modelName, self.modelVersion )
		global modelDetectionHelpers
		if not modelDetectionHelpers.get( self.modelDir ):
			modelDetectionHelper = ModelDetectionHelper.ModelDetectionHelper( self.modelDir )
			modelDetectionHelpers[ self.modelDir ] = modelDetectionHelper

	def process( self, frame ):
		score = modelDetectionHelpers[ self.modelDir ].classifyImage( frame.imgName )
		return score, True

	def __str__( self ):
		return "%s:%s:%s" % ( self.name, self.modelName, self.modelVersion )
