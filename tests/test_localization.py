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

from PIL import Image, ImageDraw

from infra.Pipeline import Pipeline
from config.Config import Config
from config.Status import Status
from config.Version import Version

class Statistics( object ):
  def __init__( self ):
    self.frame = None
    self.annotations = None
    self.annotationPosition = {}
    self.localizationDetected = False
    self.overlap = 0
    self.enclose = 0
    self.areaRatio = 0
    self.centerDistance = 0
    self.multipleAnnotation = False


class StatisticTask( object ):
  def __init__( self, config, status ):
    self.config = config
    self.status = status

  def __call__( self, annotations, localizations ):
    self.annotations = annotations
    self.localizations = localizations
    print 'Generate Stats'


class RandomRectTask( Task ):
  def __call__( self, obj ):
    x, y, area, ratio, positionstep, frameWidth, frameHeight  = obj
    gen = RandomRectGenerator( x, y, area, ratio, positionstep, frameWidth, frameHeight )
    config = self.config
    status = self.status
    for aRect in gen:
      frame = Frame( config.ci_allClassIds,
          len( config.allCellBoundariesDict[ "patchMapping" ] ),
          config.ci_scoreTypes.keys() )
      caffe = MockCaffeModel( config, aRect )
      caffe.scoreFrame( frame )
      classFilter = ClassFilter( config, status )
      zDist = ZDistFilter( config, status )
      localization = Localization( config, status )
      result = localization( classFilter( ( frame, config.ci_allClassIds ) ) )
      for classId, ls in result[ 0 ].localizations.items():
        for l in ls:
          assert str( classId ) == '0'
          print '%s for annotation %s' % ( l, aRect )
    return None

class RandomRectGenerator( object ):
  def __init__( self, x, y, area, ratio, positionstep, frameWidth, frameHeight ):
    self.areaConstraint = area
    self.x = x
    self.y = y
    self.frameWidth = frameWidth
    self.frameHeight = frameHeight
    self.positionstep = positionstep
    self.minBreadth = math.sqrt( area/ratio )
    self.maxLength = area/self.minBreadth

    # Iterator States
    self.w = self.minBreadth
  
  def __iter__( self ):
    return self
  
  def next( self ):
    self.w = int( self.w + self.positionstep )
    if self.w >= self.maxLength:
      raise StopIteration
    h = int( self.areaConstraint / self.w )
    r2 = Rect(
        self.x,
        self.y,
        self.w,
        h )
    return r2

class RandomAnnotation( object ):
  def __init__( self, config ):
    self.patchWidth = config.sw_patchWidth
    self.patchHeight = config.sw_patchHeight
    self.frameWidth = config.sw_frame_width
    self.frameHeight = config.sw_frame_height
    self.patchArea = ( self.patchWidth * self.patchHeight )
    self.classIds = config.ci_allClassIds
    self.scale = 1

  def randomAnnotation( self ):
    ratioToPatchArea = random.uniform(0.05, 1.5)
    areaOfRandomRect = ( self.patchArea * ratioToPatchArea )
    # Assuming a square annotation for now
    lengthOfRect = int( math.sqrt( areaOfRandomRect ) )
    x = random.randrange( 0, self.frameWidth - lengthOfRect )
    y = random.randrange( 0, self.frameHeight  - lengthOfRect)
    return ( Rect( x, y, lengthOfRect, lengthOfRect ), random.choice( self.classIds ) )

class MockCaffeModel( object ):

  def __init__( self, config, aRect ):
    self.cellBoundariesDict = config.allCellBoundariesDict
    self.patchMapping = self.cellBoundariesDict[ "patchMapping" ]
    self.classIds = config.ci_allClassIds
    self.aRect = aRect

  def rectIntersect( self, patchDim ):
    scale = patchDim[ 0 ]
    patchRect = Rect(
        patchDim[ 1 ]/scale, 
        patchDim[ 2 ]/scale,
        patchDim[ 3 ]/scale - patchDim[ 1 ]/scale, 
        patchDim[ 4 ]/scale - patchDim[ 2 ]/scale
        )
    areaIntersect = patchRect.intersect( self.aRect )
    return areaIntersect > ( 0.8 * self.aRect.area )

  def probPatch( self, patchDim ):
    if self.rectIntersect( patchDim ):
      prob = np.zeros(  ( 1, len( self.classIds ) ) )
      prob[ 0, 0 ] = 1
    else:
      prob = np.random.random( ( 1, len( self.classIds ) ) )
      prob = prob / np.sum( prob )
    return prob

  def fc8Patch( self, patchDim ):
    prob = np.random.random( ( 1, len( self.classIds ) ) )
    prob = prob / np.sum( prob )
    return prob

  def scoreFrame( self, frame ):
    # Generate Prob Scores
    # Generate Fc8 Scores
    for patchDim, patchId in self.patchMapping.iteritems():
      frame.scores[ 0 ] [ patchId, :, 0 ] = self.probPatch( patchDim )
      frame.scores[ 0 ] [ patchId, :, 1 ] = self.fc8Patch( patchDim )
    
AREASTEP = 0.5
AREARATIO = 5.0
POSITIONSTEP = 10
WIDTH = 1280
HEIGHT = 720

def mainGenerateRectangles( configFileName ):
  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.Queue()
  config = Config( configFileName )
  status = Status( config )
  myPipeline = Pipeline(
      [ RandomRectTask( config, status ) ], inputs, results )
  myPipeline.start()
  #rectangles = []
  areaConstraint = 0.05
  while areaConstraint <= 1.5:
    for x in range( 0, WIDTH, POSITIONSTEP ):
      for y in range( 0, HEIGHT, POSITIONSTEP ):
        #gen = RandomRectGenerator( x, y, areaConstraint * ( 256 * 256 ),
        #    AREARATIO, POSITIONSTEP, WIDTH, HEIGHT )
        #for aRect in gen:
        #  rectangles.append( aRect.asNumpy() )
        inputs.put( 
        ( x, y, areaConstraint * ( 256 * 256 ), AREARATIO, POSITIONSTEP, WIDTH, HEIGHT ) )
    areaConstraint += AREASTEP
  #rectArray = np.zeros( ( 1, len( rectangles ) ), dtype=aRect.numpyType )
  #i = 0
  #for r in rectangles:
  #  rectArray[ 0, i ] = r 
  #  i +=1 
  #np.save( open( '/tmp/rectangles.npy', 'wb' ), rectArray )
  #import pdb; pdb.set_trace()
  myPipeline.join()
 
def generateStats():
  st = StatisticTask( None, None )
  annotations = []
  frames = []
  print st( annotations, frames )

  
if __name__=="__main__":
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[ 0 ]
    sys.exit(1)
  startTime = time.time()
  #logging.basicConfig(
  #    format=
  #    '{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
  #    level=logging.INFO,
  #    datefmt="%Y-%m-%d--%H:%M:%S")
  mainGenerateRectangles( sys.argv[ 1 ] )
  time.sleep( 1 )
  print 'Took %s' % ( time.time() - startTime )

