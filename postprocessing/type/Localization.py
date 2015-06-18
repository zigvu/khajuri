import sys


class Localization(object):

  def __init__(self, zDistThreshold, classId, rect, score, scale):
    self.zDistThreshold = zDistThreshold
    self.classId = classId
    self.rect = rect
    self.score = score
    self.scale = scale

  def __str__(self):
    return 'Localization(%s, %s, %s)' % (
        self.zDistThreshold, self.classId, self.rect
    )

  def matchClosestLocalization(self, other):
    # Lower the better value
    matchValue = sys.maxint
    if self.zDistThreshold == other.zDistThreshold and \
        self.classId == other.classId and \
        self.scale == other.scale:
      matchValue = self.rect.centerDistance(other.rect)
    return matchValue
