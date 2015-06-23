from config.Config import Config
from postprocessing.type.Frame import Frame
from postprocessing.type.Rect import Rect
import sys, random, math, logging
import numpy as np

from postprocessing.task.Task import Task
from postprocessing.task.ClassFilter import ClassFilter
from postprocessing.task.ZDistFilter import ZDistFilter
from postprocessing.task.JsonReader import JsonReader
from postprocessing.task.JsonWriter import JsonWriter
from postprocessing.task.OldJsonReader import OldJsonReader
from postprocessing.task.Localization import Localization

from PIL import Image, ImageDraw

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

  def __init__( self, config, aRect, aRectClassId ):
    self.classIds = config.ci_allClassIds
    self.cellBoundariesDict = config.allCellBoundariesDict
    self.patchMapping = self.cellBoundariesDict[ "patchMapping" ]
    self.aRect = aRect
    self.aRectClassId = aRectClassId

  def rectIntersect( self, patchDim ):
    scale = patchDim[ 0 ]
    patchRect = Rect(
        patchDim[ 1 ]/scale, 
        patchDim[ 2 ]/scale,
        patchDim[ 3 ]/scale - patchDim[ 1 ]/scale, 
        patchDim[ 4 ]/scale - patchDim[ 2 ]/scale
        )
    return patchRect.intersect( self.aRect )

  def probPatch( self, patchDim ):
    if self.rectIntersect( patchDim ):
      prob = np.zeros(  ( 1, len( self.classIds ) ) )
      prob[ 0, int( self.aRectClassId ) ] = 1
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
    
def test_localization( configFileName ):
  config = Config( configFileName )
  status = None
  htmlFile = open( "result.html", "w" )
  for i in range( 10 ):
    rA = RandomAnnotation( config )
    frame = Frame( config.ci_allClassIds, len( config.allCellBoundariesDict[ "patchMapping" ] ),
        config.ci_scoreTypes.keys() )
    aRect, aRectClassId = rA.randomAnnotation()
    caffe = MockCaffeModel( config, aRect, aRectClassId )
    im = Image.new("RGB",
        ( config.sw_frame_width, config.sw_frame_height ) )
    dr = ImageDraw.Draw(im)
    dr.rectangle( ( aRect.x, aRect.y, aRect.x + aRect.w, aRect.y + aRect.h ) , outline="red" )
    caffe.scoreFrame( frame )
    classFilter = ClassFilter( config, status ),
    zDist = ZDistFilter( config, status ),
    localization = Localization( config, status )
    result = localization( zDist[0]( classFilter[0]( ( frame, config.ci_allClassIds ) ) ) )
    for classId, ls in result[ 0 ].localizations.items():
      for l in ls:
        print 'Localization is %s for class %s' % ( l, classId )
        dr.rectangle( ( l.rect.x, l.rect.y,
          l.rect.x + l.rect.w, l.rect.y + l.rect.h ) , outline="green" )

    im.save( "frame_%s.png" % i )
    htmlFile.write( "<img src='frame_%s.png' ></img><br><p>NextImage<p>" % i )

if __name__=="__main__":
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[ 0 ]
    sys.exit(1)

  test_localization( sys.argv[ 1 ] )
