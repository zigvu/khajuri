import logging, json
import numpy as np

from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect
from Logo.PipelineMath.PixelMap import PixelMap

class GenerateCellMap( Task ):
  def __call__( self, obj ):
    scale, patchScores = obj
    logging.info( 
        'Starting patchScores to cellMap translation for patchScores %s at scale %s'
        % ( patchScores, scale ) )
    pixelMap = PixelMap( self.config.allCellBoundariesDict, scale )
    pixelMap.addScore( patchScores )
    return pixelMap.cellValues
