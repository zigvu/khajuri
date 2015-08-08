import math, random, logging
from postprocessing.type.Rect import Rect
from tests.AnnotatedFrame import AnnotatedFrame

import numpy as np
import time

AREASTEP = 0.10
AREARATIO = 3
POSITIONSTEP = 10
areaConstraintMax = 1.5
MAXANNOTATIONPERFRAME = 5
MAXDETECTABLELEN = ( 256.0/0.4 )

class RandomAnnotationGenerator( object ):
  def __init__( self, config ):
    self.config = config
    self._annotations = []
    patchArea = config.sw_patchHeight * config.sw_patchWidth
    areaConstraint = 0.05
    while areaConstraint <= areaConstraintMax:
      for x in range( 0, config.sw_frame_width, POSITIONSTEP ):
        for y in range( 0, config.sw_frame_height, POSITIONSTEP ):
          gen = RandomRectGenerator( x, y, areaConstraint * patchArea,
              AREARATIO, POSITIONSTEP,
              config.sw_frame_width, config.sw_frame_height )
          for aRect in gen:
            self._annotations.append( aRect )
      areaConstraint += AREASTEP
    
    # Convert to numpy based array
    self.numpyAnnotations = np.zeros( (1, len( self._annotations ) ),
        dtype=self._annotations[0].numpyType )
    for i, a in enumerate(self._annotations):
      self.numpyAnnotations[ 0, i] = a.asNumpy()
    self.usedIndexes = set()
    self.frameNum = 0

  def __iter__( self ):
    return self
  
  def next( self ):
    logging.info( 'Getting next annotation set' )
    annotatedFrame = AnnotatedFrame( )
    numOfAnnotations = random.randint( 1, MAXANNOTATIONPERFRAME )
    while numOfAnnotations > 0:
       logging.info( 'Len of annotations %s' % len( self._annotations ) )
       rndIndex = random.randint( 0, len( self._annotations ) - 1 )
       if rndIndex in self.usedIndexes:
         logging.info( 'Random index %s already used' % rndIndex  )
         continue
       rndAtn = self.numpyAnnotations[ 0, rndIndex ]
       myRect = Rect(rndAtn[0], rndAtn[1], rndAtn[2], rndAtn[3] )
       intersects = False
       for a in annotatedFrame.annotations:
         if myRect.intersect( a ):
           intersects = True
       if intersects:
         continue
       if myRect.h >= MAXDETECTABLELEN \
           or myRect.w >= MAXDETECTABLELEN:
         continue
       annotatedFrame.addAnnotation( myRect )
       self.usedIndexes.add( rndIndex )
       numOfAnnotations -= 1
    annotatedFrame.frameNum = self.frameNum
    self.frameNum += 1
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
