import logging, json
import numpy as np

from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

class JsonWriter( Task ):
  def __call__( self, obj ):
    frame, classIds = obj
    logging.info( 'Saving frameInfo on %s for classes %s' %
        ( frame, classIds ) )
    return ( frame, classIds )


