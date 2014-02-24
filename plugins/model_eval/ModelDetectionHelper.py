#!/usr/bin/env python
from ctypes import *
import os, json, argparse
import pdb

from plugins.Plugin import Plugin
from plugins.Plugin import VisionDetection

zsvm = None
baseScriptDir = os.path.dirname(os.path.realpath(__file__))

class Model(Structure):
  pass

class Class(Structure):
  pass

class ModelDetectionHelper( object ):
  def __init__( self, modelDir ):
    global zsvm
    if not zsvm:
      zsvm = cdll.LoadLibrary("%s/../../VideoReader/libzsvm.so" % baseScriptDir )
      zsvm.initModel.restype = POINTER( Model )
      zsvm.loadClasses.restype = POINTER( Class )
      zsvm.testImage.argtypes = [ POINTER( Model ), POINTER( Class ), c_char_p ]
      zsvm.loadClasses.argtypes = [ c_char_p ]
    self.modelDir = modelDir
    self.model = zsvm.initModel( self.modelDir + os.path.sep + "model.txt" )
    self.modelclass = zsvm.loadClasses( self.modelDir + os.path.sep + "classes.txt" )
    self.predFile = "/tmp/%d.pred.score" % os.getpid() 

  def classifyImage( self, imageFileName ):
    zsvm.testImage( self.model, self.modelclass, imageFileName, self.predFile )
    # Read score from the prediction file and output it
    f = open( self.predFile, "r" )
    predictions = json.load( f )
    f.close()
    return float( predictions[ "ground_truth" ] ["score" ] ) 

modelDetectionHelpers = {}
class ModelDetection(VisionDetection):
	"""Model Detection Plugin."""
	def __init__(self, config):
		VisionDetection.__init__(self, config)
		self.modelName = config[ 'modelName' ]
		self.modelId = config[ 'id' ]
		self.name = "%s:%s:%s" % ( "ModelDetection", self.modelName, self.modelId )
		self.modelDir = "structSVM-data/datasets/%s.%s/models/" % ( self.modelName, self.modelId )
		global modelDetectionHelpers
		if not modelDetectionHelpers.get( self.modelDir ):
			modelDetectionHelper = ModelDetectionHelper( self.modelDir )
			modelDetectionHelpers[ self.modelDir ] = modelDetectionHelper

	def process( self, frame ):
		score = modelDetectionHelpers[ self.modelDir ].classifyImage( frame.imgName )
		return score, True

	def __str__( self ):
		return "%s:%s:%s" % ( self.name, self.modelName, self.modelId )
