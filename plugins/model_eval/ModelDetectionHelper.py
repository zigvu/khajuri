#!/usr/bin/env python
from ctypes import *
import os, json, argparse
import pdb

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
