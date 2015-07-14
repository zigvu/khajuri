import sys

class SingleFrameStatistics( object ):
  def __init__( self, frameWidth, frameHeight, annotatedFrame ):
    self.frameWidth = frameWidth
    self.frameHeight = frameHeight
    self.annotatedFrame = annotatedFrame
    self.numOfAnnotations = len( self.annotatedFrame.annotations )

    localizations = []
    for classId, ls in self.annotatedFrame.frame.localizations.items():
       for l in ls:
         localizations.append( l.rect )
    self.numOfLocalizations = len( localizations )


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
      if a.x >= frameWidth - 50 or a.y >= frameHeight - 50 or \
                a.x <= 50 or a.y <= 50:
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
    distanceSum = 0
    for a in self.annotatedFrame.annotations:
      self.annotationToLocalization[ a ] = ( None, sys.maxint )
      for l in localizations:
         distance = a.centerDistance( l )
         if distance < self.annotationToLocalization[ a ][ 1 ]:
           self.annotationToLocalization[ a ] = ( l, distance )
      distanceSum +=  self.annotationToLocalization[ a ][1]

    self.avGcenterDistance = distanceSum/len(self.annotatedFrame.annotations)

    # Missing Localization
    # Area Ratios
    self.missingLocalization = []
    self.areaRatioByAnnotation = {}
    for a, ( l, d ) in self.annotationToLocalization.items():
      if l.intersect( a ) <= 0.1 * a.area:
        self.missingLocalization.append( a )
      else:
        self.areaRatioByAnnotation[ a ] = a.area/l.area

    # Localization with no Annotation
    self.missingAnnotations = []
    for l in localizations:
      self.missingAnnotations.append( l )
      for a in self.annotatedFrame.annotations:
         if l.intersect( a ) >= 0.1 * a.area:
           self.missingAnnotations.remove( l )
           break
