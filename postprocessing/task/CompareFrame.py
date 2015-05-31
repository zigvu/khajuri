import logging, json, os

from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

class CompareFrame( Task ):

  def __call__( self, obj ):
    frame1, frame2 = obj
    logging.info( 'Comparing frame1 %s and frame2 %s with formats' % ( frame1, frame2 ) )
    scoreDiff = frame1.getScoreDiff(frame2)
    localizationDiff = frame1.getLocalizationDiff(frame2)
    logging.info( 'Score diff: %s' % scoreDiff )
    logging.info( 'Localization diff: %s' % localizationDiff )
    return ( frame1, scoreDiff, localizationDiff )
