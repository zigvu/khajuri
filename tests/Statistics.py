import sys
import numpy as np

class Statistics( object ):
  def __init__( self, config ):
    self.stats = {}
    self.frameNum = 0
    self.numOfAnnotations = []
    self.numOfLocalizations = []
    self.statsWithCornerAnnotation = []
    self.statsWithMissingLocalization = []
    self.statsWithExtraLocalization = []
    self.areaRatio = []
    self.centerDistance = []
    self.enclosed = []

  def addFrameStats( self, frameStats ):
    self.stats[ self.frameNum ] = frameStats
    self.frameNum += 1
    self.numOfLocalizations.append( frameStats.numOfLocalizations )
    self.numOfAnnotations.append( frameStats.numOfAnnotations )
    if frameStats.corner:
      self.statsWithCornerAnnotation.append( frameStats )
    if len( frameStats.missingLocalization ) > 0:
      self.statsWithMissingLocalization.append( frameStats )
    if len( frameStats.missingAnnotations ) > 0:
      self.statsWithExtraLocalization.append( frameStats )
    self.areaRatio += frameStats.areaRatioByAnnotation.values()
    self.centerDistance.append( frameStats.avGcenterDistance )
    if frameStats.overAllEnclosed:
      self.enclosed.append( frameStats )

 
  def printStat( self ):
    print 'Evaluated: %s frames' % len( self.stats )
    print 'Evaluated: %s annotations' % np.sum( self.numOfAnnotations )
    print 'Produced: %s localization' % np.sum( self.numOfLocalizations )
    print 'At least one cornered annotation: %s frames' % len( self.statsWithCornerAnnotation )
    print 'Missing localization: %s annotations' % len( self.statsWithMissingLocalization )
    print 'Extra localization: %s' % len( self.statsWithExtraLocalization )
    print 'Enclosed annotations: %s frames' % len( self.enclosed )
    print 'Histogram of Annotations Count %s, buckets: %s' % np.histogram( self.numOfAnnotations, bins=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] )
    print 'Histogram of Localizations Count %s, buckets: %s' % np.histogram( self.numOfLocalizations, bins=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ] )
    print 'Histogram of Area Ratio( anno/loca ) %s, buckets: %s' % np.histogram( self.areaRatio, bins=5 )
    # Center Distance Histogram
    print 'Histogram of Center Distances %s, buckets: %s' % np.histogram( self.centerDistance, bins=[0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 ] )
    # Save
