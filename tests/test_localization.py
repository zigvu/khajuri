from config.Config import Config
from postprocessing.type.Frame import Frame
from postprocessing.type.Rect import Rect
import sys, random, math, logging
import multiprocessing, time, os, logging
import numpy as np

from postprocessing.task.Task import Task
from postprocessing.task.ClassFilter import ClassFilter
from postprocessing.task.ZDistFilter import ZDistFilter
from postprocessing.task.JsonReader import JsonReader
from postprocessing.task.JsonWriter import JsonWriter
from postprocessing.task.OldJsonReader import OldJsonReader
from postprocessing.task.Localization import Localization

from infra.Pipeline import Pipeline
from config.Config import Config
from config.Status import Status
from config.Version import Version

from tests.RandomRectGenerator import RandomRectGenerator
from tests.MockLocalizationTask import MockLocalizationTask
from tests.AnnotatedFrame import AnnotatedFrame
from tests.SingleFrameStatistics import SingleFrameStatistics


def mainGenerateRectangles( configFileName ):
  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.Queue()
  config = Config( configFileName )
  status = Status( config )
  rectangles = []
  AREASTEP = 0.5
  AREARATIO = 2.0
  POSITIONSTEP = 50
  areaConstraint = 0.05
  areaConstraintMax = 1.5
  patchArea = config.sw_patchHeight * config.sw_patchWidth
  while areaConstraint <= areaConstraintMax:
    for x in range( 0, config.sw_frame_width, POSITIONSTEP ):
      for y in range( 0, config.sw_frame_height, POSITIONSTEP ):
        gen = RandomRectGenerator( x, y, areaConstraint * patchArea,
            AREARATIO, POSITIONSTEP,
            config.sw_frame_width, config.sw_frame_height )
        for aRect in gen:
          rectangles.append( aRect )
    areaConstraint += AREASTEP
  print 'Number of rectangles %s' % len( rectangles )
  while len( rectangles ) > 0:
     myTask = MockLocalizationTask( config, status ) 
     annotatedFrame = AnnotatedFrame( config )
     i = random.randint( 0, len( rectangles ) )
     j = random.randint( 0, len( rectangles ) )
     annotatedFrame.addAnnotation( rectangles[ i ] )
     annotatedFrame.addAnnotation( rectangles[ j ] )
     rectangles.remove( rectangles[ i ] )
     rectangles.remove( rectangles[ j ] )
     myTask( annotatedFrame )
     print SingleFrameStatistics( config, annotatedFrame )
 
if __name__=="__main__":
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[ 0 ]
    sys.exit(1)
  mainGenerateRectangles( sys.argv[ 1 ] )
