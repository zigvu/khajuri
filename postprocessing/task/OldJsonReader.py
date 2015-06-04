import logging, json
import numpy as np
import os

from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

class OldJsonReader( Task ):

  def getVideoId( self, jsonFileName ):
    baseName = os.path.basename( jsonFileName )
    return baseName.split( '_' )[0]

  def getPatches( self, scale ):
    # Patch Scores
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        return obj[ 'patches' ]

  def getClassIds( self ):
    classIds = self.myDict['scales'][0]['patches'][0]['scores'].keys()
    return classIds

  def __call__( self, obj ):
    fileName = obj
    logging.info( 'Reading frameInfo from %s' % fileName )
    if not self.config.videoId:
      self.config.videoId = self.getVideoId( fileName )
    self.myDict = json.load( open( fileName, 'r' ) )
    frame = Frame( self.config.ci_allClassIds, 543, self.config.ci_scoreTypes.keys() )
    frame.frameNumber = self.myDict[ "frame_number" ]
    self.patchMapping = self.config.allCellBoundariesDict[ "patchMapping" ]
    self.classIds =  self.getClassIds()
    scores = np.zeros(( len( self.patchMapping.keys() ), len( self.classIds ) ) )
    fc8scores = np.zeros(( len( self.patchMapping.keys() ), len( self.classIds ) ) )
    for scale in self.config.sw_scales:
      for patch in self.getPatches( scale ):
        x = patch[ "patch" ]["x"]
        y = patch[ "patch" ]["y"]
        w = patch[ "patch" ]["width"]
        h = patch[ "patch" ]["height"]
        patchId = self.patchMapping[ ( scale, x, y, x + w , y + h  ) ]
        for classId in self.classIds:
          scores[ patchId, classId ] = patch[ "scores" ] [ classId ]
          fc8scores[ patchId, classId ] = patch[ "scores_fc8" ] [ classId ]

    frame.scores[ 0 ][ :, :, 0 ] = scores
    frame.scores[ 0 ][ :, :, 1 ] = fc8scores
    return ( frame, self.classIds )