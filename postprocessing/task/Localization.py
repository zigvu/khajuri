import logging, json
import numpy as np
from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

from config.Config import Config
from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.PixelMapper import PixelMapper
from Logo.PipelineMath.FramePostProcessor import FramePostProcessor
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.PixelMap import PixelMap

class Localization( Task ):

  def __call__( self, obj ):
    frame, classIds = obj
    for zDistThreshold in self.config.pp_zDistThresholds:
      for classId in classIds:
        logging.info( 'Localize on %s for class %s at zDist: %s' % ( frame, classId, zDistThreshold ) )
        frameLocalizer = FramePostProcessor( classId, self.config, frame, zDistThreshold )
        frameLocalizer.localize()

    return ( frame, classIds )
