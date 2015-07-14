#!/usr/bin/env python
import math, random
import numpy as np
class Rect( object ):
  def __init__( self, x, y, w, h ):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.center = ( x + w/2.0, y + h / 2.0 )
    self.A = w * h
    self._numpyType =  np.dtype( [
                          ('x', np.ushort),
                          ('y', np.ushort),
                          ('w', np.ushort),
                          ('h', np.ushort) ] )

  def __str__( self ):
    return 'Rect(%s, %s, %s, %s, %s)' % ( self.x, self.y, self.w, self.h, self.area )

  @property
  def area( self ):
    return self.w * self.h
  
  @property
  def numpyType( self ):
    return self._numpyType

  def asNumpy( self ):
    rect = self.numpyType
    x = np.array( [ ( self.x, self.y, self.w, self.h ) ], dtype=rect )
    return x


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
      x_overlap = max(0, min(RectAX2,RectBX2) - max(RectAX1,RectBX1));
      y_overlap = max(0, min(RectAY2,RectBY2) - max(RectAY1,RectBY1));
      area = x_overlap * y_overlap;
      return area

    return 0
