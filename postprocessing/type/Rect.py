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

  def centerDistance(self, other):
    distanceSquaredSum = ((self.center[0] - other.center[0]) ** 2) + \
        ((self.center[1] - other.center[1]) ** 2)
    return math.sqrt(distanceSquaredSum)
