#!/usr/bin/python
import glob, sys
import os, tempfile, pdb
import yaml, json
from LogoPipeline import AnnotationsReader
from collections import OrderedDict
 
class Predictor( object ):
  def __init__( self, config ):
    self.config = config
    self.frameScores = {}
    self.reader = {}
    self.inputDir = self.config.getInputDir()
    self.outputDir = self.config.getOutputir()
    annotationsFiles = os.path.join( self.inputDir, "annotations", "*json" )
    jsonFiles = glob.glob( annotationsFiles )
    for f in jsonFiles:
      reader = AnnotationsReader( f )
      self.reader[ reader.getFrameNumber() ] = reader
      self.reader[ reader.getFrameNumber() ].myDict[ "frame_scores" ]\
          = OrderedDict()

    self.listOfClassIds = self.reader[ 1 ].getClassIds()
    self.scalingFactors = self.reader[ 1 ].scalingFactors
    # Testing
    #self.saveScore( 1, '0', 0.25 )
    #self.saveScore( 1, '1', 0.75 )
    #self.saveResults()
    #pdb.set_trace()
 
  def getFrameIds( self ):
    return self.reader.keys()
 
  def getClassIds( self ):
    return self.listOfClassIds

  def getScalingFactors( self ):
    return self.scalingFactors
  
  def getPatches( self, frameId, scale ):
    patches = {}
    i = 0
    for patch in self.reader[ frameId ].myDict['scales'][ self.scalingFactors.index( scale ) ]['patches']:
      patches[ i ] = patch['patch']
      i += 1
    return patches
  
  def getScore( self, frameId, patchId, classId, scale ):
    return self.reader[ frameId ].getScoreForPatchIdAtScale( patchId, classId, scale )
 
  def run( self ):
    raise NotImplementedError( "TODO - Amit - fill in the implementation " )
 
  def saveScore( self, frameId, classId, score ):
    self.frameScores[ ( frameId, classId ) ] = score
 
  def saveResults( self ):
    for ( frameId, classId ), score in self.frameScores.iteritems():
      frame_score = self.reader[ frameId ].myDict[ "frame_scores" ]
      frame_score[ classId ] = score
      outputDir = os.path.join( self.outputDir, self.config.getDirToSavePredictions() )
      if not os.path.exists( outputDir ):
        os.makedirs( outputDir )
      outputFileName = os.path.join( outputDir,
          self.reader[ frameId ].getAnnotationFileName() )
      with open( outputFileName, "w" ) as f :
        json.dump( self.reader[ frameId ].myDict, f, indent=2 )
