import sys

class SingleFrameStatistics( object ):
  def __init__( self, config, annotatedFrame ):
    self.annotatedFrame = annotatedFrame
    self.numOfAnnotations = len( self.annotatedFrame.annotations )
    self.numOfLocalizations = len( self.annotatedFrame.frame.localizations )

    localizations = []
    for classId, ls in self.annotatedFrame.frame.localizations.items():
       for l in ls:
         localizations.append( l.rect )


    # Multiple Annotations and Localizations
    # Their Area Ratio
    self.annotatedArea = 0.0
    for a in self.annotatedFrame.annotations:
       self.annotatedArea += a.area
    self.localizationArea = 0.0
    for l in localizations:
       self.localizationArea += l.area
    self.areaRatio = self.localizationArea/self.annotatedArea

    # Corner or Central?
    self.corner = False
    for a in self.annotatedFrame.annotations:
      if a.x >= config.sw_frame_width  - 100 or a.y >= config.sw_frame_height - 100:
        self.corner = True
        break

    # Enclosed?
    self.enclosed = {}
    for a in self.annotatedFrame.annotations:
       self.enclosed[ a ] = False
       for l in localizations:
          if a.intersect( l ) == a.area:
             self.enclosed[ a ] = True
    self.overAllEnclosed = all( self.enclosed.values() )


    # Calculate all distances
    # Choose the smallest for each annotations and sum them up
    self.annotationToLocalization = {}
    for a in self.annotatedFrame.annotations:
      self.annotationToLocalization[ a ] = ( None, sys.maxint )
      for l in localizations:
         distance = a.centerDistance( l )
         if distance < self.annotationToLocalization[ a ][ 1 ]:
           self.annotationToLocalization[ a ] = ( l, distance )
    self.centerDistance = 0

    print 'Annotation Area %s' % self.annotatedArea
    print 'Localization Area %s' % self.localizationArea
    print 'Area Ratio %s' % ( self.areaRatio )
    print 'Corner %s' % ( self.corner )
    print 'Enclosed %s' % ( self.overAllEnclosed )
    print 'Distances %s' % ( self.annotationToLocalization.items() )
  
  def __str__( self ):
    return 'SingleFrameStatistics( annotations: %s, localizations: %s, enclosed: %s, corner: %s, centerDistance: %s )' % \
          ( self.numOfAnnotations, self.numOfLocalizations,
            self.enclosed, self.corner, self.centerDistance )

