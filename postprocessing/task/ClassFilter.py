import logging, json
import numpy as np

from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

class ClassFilter( Task ):
  def __call__( self, obj ):
    frame, classIds = obj
    logging.info( 'Starting Class Filter on %s for classes %s' %
        ( frame, classIds ) )
    return self.splitUsingThreshold( frame, classIds, 0 )

  def splitUsingThreshold( self, frame, classIds, zDist ):
    threshold = self.config.pp_detectorThreshold
    maxArray = np.amax( frame.scores[ zDist ][ :, :, 0 ], axis=0)
    above = set( np.argwhere( maxArray > threshold ).flatten() )
    logging.info( 'Reduce list size from %s to %s' %
       ( len( classIds ), len( above ) ) )
    return ( frame, above )
