import math

from postprocessing.type.Rect import Rect

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
