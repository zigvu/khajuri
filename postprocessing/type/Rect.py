class Rect( object ):
  def __init__( self, x, y, w, h ):
    self.x = x
    self.y = y
    self.w = w
    self.h = h

  def __str__( self ):
    return 'Rect(%s, %s, %s, %s)' % ( self.x, self.y, self.w, self.h )
