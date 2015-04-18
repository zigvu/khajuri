import logging, json
import numpy as np

from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

class ZDistFilter( Task ):
  def __call__( self, obj ):
    frame, classIds = obj
    logging.info( 'Starting ZDist on %s for classes %s' %
        ( frame, classIds ) )
    for zDistThreshold in self.config.pp_zDistThresholds:
       self.zDistScore( frame, zDistThreshold )
    return ( frame, classIds )

  def zDistScore( self, frame, zDistThreshold ):
    probScores = frame.scores[0][ :, :, 0 ]
    frame.scores[ zDistThreshold ] = frame.initNumpyArrayScore()
    for probScore in probScores:
       sortedScores = sorted( probScore )
       zDist = np.std(sortedScores) - np.std(sortedScores[1:])
       if zDist >= zDistThreshold:
          frame.scores[ zDistThreshold ] = probScore
