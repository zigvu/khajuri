from random import random
import os, sys
from Controller.Config import Config

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

class Bunch(dict):
  def __init__(self, *args, **kw):
    super(Bunch, self).__init__(*args, **kw)
    self.__dict__ = self

class StandAlonePlugin( object ):
  def __init__( self, pluginClass, pluginName ):
     self.PluginClass = pluginClass
     self.name = pluginName

  def process( self, imgFile ):
     baseScriptDir = os.path.dirname(os.path.realpath(__file__))
     configFile = os.path.join( baseScriptDir, "..", "default_config.yaml" )
     myConfig = Config( configFile )
     plugin = self.PluginClass( myConfig.getPluginConfig( self.name ) )
     frame = Bunch()
     frame.imgName = sys.argv[ 1 ]
     return plugin.process( frame )
