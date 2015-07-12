import sys

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
    self.areaRatio.append( frameStats.areaRatioByAnnotation.values() )
    self.centerDistance.append( frameStats.avGcenterDistance )

 
  def printStat( self ):
    print 'Number of Frame Evaluated: %s' % len( self.stats )
    # Num of frame with Corner 
    print 'Number of Frame with cornered annotation: %s' % len( self.statsWithCornerAnnotation )
    # Num of Frames with missing Localization
    print 'Number of Frame with missing localization: %s' % len( self.statsWithMissingLocalization )
    # Num of Frames with useless Localization
    print 'Number of Frame with extra localization: %s' % len( self.statsWithExtraLocalization )
    # Area Ratio Histogram
    # Center Distance Histogram
    # Save
