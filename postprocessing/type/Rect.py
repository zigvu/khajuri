import math


class Rect(object):

  def __init__(self, x, y, w, h):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.center = (x + w / 2.0, y + h / 2.0)
    self.A = w * h

  def __str__(self):
    return 'Rect(%s, %s, %s, %s)' % (self.x, self.y, self.w, self.h)

  def centerDistance( self, other ):
    distanceSquaredSum = ( ( self.center[ 0 ] - other.center[ 0 ] ) ** 2 ) + \
        ( ( self.center[ 1 ] - other.center[ 1 ] )  ** 2 )
    return math.sqrt( distanceSquaredSum )

  def intersect( self, other ):
    RectAX1 = self.x
    RectAX2 = self.x + self.w
    RectAY1 = self.y
    RectAY2 = self.y + self.h

    RectBX1 = other.x
    RectBX2 = other.x + other.w
    RectBY1 = other.y
    RectBY2 = other.y + other.h

    if (RectAX1 < RectBX2 and RectAX2 > RectBX1 and RectAY1 < RectBY2 and RectAY2 > RectBY1):
      return True

    return False
