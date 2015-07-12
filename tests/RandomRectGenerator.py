import math, random
from postprocessing.type.Rect import Rect
from tests.AnnotatedFrame import AnnotatedFrame

AREASTEP = 0.5
AREARATIO = 2.0
POSITIONSTEP = 50
areaConstraintMax = 1.5
MAXANNOTATIONPERFRAME = 5.0

class RandomAnnotationGenerator( object ):
  def __init__( self, config ):
    self.config = config
    self.annotations = []
    patchArea = config.sw_patchHeight * config.sw_patchWidth
    areaConstraint = 0.05
    while areaConstraint <= areaConstraintMax:
      for x in range( 0, config.sw_frame_width, POSITIONSTEP ):
        for y in range( 0, config.sw_frame_height, POSITIONSTEP ):
          gen = RandomRectGenerator( x, y, areaConstraint * patchArea,
              AREARATIO, POSITIONSTEP,
              config.sw_frame_width, config.sw_frame_height )
          for aRect in gen:
            self.annotations.append( aRect )
      areaConstraint += AREASTEP
  def __iter__( self ):
    return self
  
  def next( self ):
    annotatedFrame = AnnotatedFrame( self.config )
    numOfAnnotations = random.randint( 1, MAXANNOTATIONPERFRAME )
    while numOfAnnotations > 0:
       rndAtn = random.choice( self.annotations )
       for a in annotatedFrame.annotations:
         if rndAtn.intersect( a ):
           break
       else:
         annotatedFrame.addAnnotation( rndAtn )
         self.annotations.remove( rndAtn )
         numOfAnnotations -= 1
    return annotatedFrame

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

  def checkBounds( self, h ):
    return self.x + self.w <= self.frameWidth and \
        self.y + h <= self.frameHeight
  
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
    # Check for bounds
    if self.checkBounds( h ):
      return r2
    else:
      return self.next()
