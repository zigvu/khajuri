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
from tests.Statistics import Statistics
from PIL import Image, ImageDraw

AREASTEP = 0.5
AREARATIO = 2.0
POSITIONSTEP = 50
areaConstraintMax = 1.5
MAXANNOTATIONPERFRAME = 5.0

def drawImage( stats, frameNum, config ):
   im = Image.new( 'RGBA', ( config.sw_frame_width, config.sw_frame_height ), ( 0, 0, 0, 0 ) )
   draw = ImageDraw.Draw(im)
   for a in stats.annotatedFrame.annotations:
     draw.rectangle( ( a.x, a.y, a.x + a.w, a.y + a.h ), outline="green" )
   for classId, ls in stats.annotatedFrame.frame.localizations.items():
       for l in ls:
         draw.rectangle( ( l.rect.x, l.rect.y, l.rect.x + l.rect.w, l.rect.y + l.rect.h ), outline="red" )
   textToDraw = [ 
       'Frame %s' % frameNum,
       'Annotation Area %s' % stats.annotatedArea,
       'Localization Area %f' % stats.localizationArea,
       'Area Ratio %s' % stats.areaRatio,
       'Corner %s' % stats.corner,
       'Enclosed %s' % stats.overAllEnclosed,
       'Avg Center Distance %s' % stats.avGcenterDistance,
       'Num Of Annotations %s' % stats.numOfAnnotations,
       'Num Of Localizations %s' % stats.numOfLocalizations,
       'Num Annotations with no Localizations %s' % len( stats.missingLocalization ),
       'Num Localization with no Annotations %s' % len( stats.missingAnnotations ),
       'Area Ratios %s' % stats.areaRatioByAnnotation.values(),
       ]
   y = 10
   for t in textToDraw:
      draw.text( ( 10, y ), t, fill="black" )
      y += 20
   im.save( "frame_%s.png" % frameNum )
