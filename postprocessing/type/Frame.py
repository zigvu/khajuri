import numpy as np
import sys

class Frame(object):
  def __init__(self, classIds, totalPatches, scoreTypes ):
    # Properties/Collections
    self.frameDisplayTime = None
    self.frameNumber = None
    zDistThreshold = 0
    self.localizations = {}
    self.totalPatches = totalPatches
    self.scoreTypes = scoreTypes
    self.classIds = classIds
    self.scores = {}
    self.scores[ zDistThreshold ] = self.initNumpyArrayScore()
    self.cellValues = {}

  def initNumpyArrayScore( self ):
    '''
    The patch scores are stored in a 3-d numpy array
    1 dim => Patch itself
    2 dim => classes
    3 dim => scoreTypes
    '''
    return np.zeros( ( self.totalPatches,
                       len( self.classIds ),
                       len( self.scoreTypes ) ), dtype=np.float )

  def getPatchMapper( self ):
    return self.patchMapper

  def addLocalization( self, classId, l ):
    if not self.localizations.get( classId ):
      self.localizations[ classId ] = []
    self.localizations[ classId ].append( l )

  def localization( self, k ):
    return self.localizations[ k ]

  def addScore( self, classId, scoreType, zDistThreshold, scores ):
    self.scores[ zDistThreshold ][ :, classId, scoreType ] = scores

  def addScores( self, patchId, scores ):
    ''' Incoming scores from caffe '''
    self.scores[ 0 ] [ patchId, :, 0 ] = scores

  def addfc8Scores( self, patchId, scores ):
    ''' Incoming fc8 scores from caffe '''
    self.scores[ 0 ] [ patchId, :, 1 ] = scores

  def __str__( self ):
    return 'Frame(%s)-(%s)' % ( self.frameNumber, self.localizations.items() )

  def getScoreDiff( self, frame ):
    diff = {}
    for classId in self.classIds:
      diff[ classId ] = {}
      diff[ classId ] [ 'min' ] = 999
      diff[ classId ] [ 'avg' ] = 0
      diff[ classId ] [ 'max' ] = -1
      scoreDiffForClass = \
          self.scores[ 0 ] [ :, int( classId ) , 0 ] - frame.scores[ 0 ][ :, int( classId ), 0 ]
      assert len( scoreDiffForClass ) == self.totalPatches
      if scoreDiffForClass.any():
        diff[ classId ] [ 'min' ] = np.min(scoreDiffForClass)
        diff[ classId ] [ 'avg' ] = np.average(scoreDiffForClass)
        diff[ classId ] [ 'max' ] = np.max(scoreDiffForClass)

    return diff

  def getLocalizationDiff( self, frame ):
    diff = {}
    for classId in self.classIds:
      diff[ classId ] = {}
      localizationListA = self.localizations.get( int( classId ) )
      localizationListB = frame.localizations.get( int( classId ) )
      filteredA = []
      filteredB = []
      if not localizationListA:
        localizationListA = []
      if not localizationListB:
        localizationListB = []
      for l in localizationListA:
        if l.zDistThreshold == 0:
          filteredA.append( l )
      for l in localizationListB:
        if l.zDistThreshold == 0:
          filteredB.append( l )

      diff[ classId ] [ 'bbox' ] = abs ( len( filteredA ) - 
          len( filteredB ) )
      diff[ classId ] [ 'maxX' ] = 0
      diff[ classId ] [ 'maxY' ] = 0
      diff[ classId ] [ 'maxA' ] = 0
      diff[ classId ] [ 'maxS' ] = -1
      if diff[ classId ] [ 'bbox' ] == 0 and len( filteredA ) > 0:
        # Check further when the number of bboxes match
        for lA in filteredA:
          bestMetric = sys.maxint
          match = None
          for lB in filteredB:
            current = lA.matchClosestLocalization( lB )
            if current < bestMetric:
              match = lB
              bestMetric = current
          if bestMetric != sys.maxint:
            diff[ classId ] [ 'maxX' ] = max( diff[ classId ] [ 'maxX' ], 
                abs( lA.rect.x - match.rect.x ) )
            diff[ classId ] [ 'maxY' ] = max( diff[ classId ] [ 'maxY' ],
                abs( lA.rect.y - match.rect.y ) )
            diff[ classId ] [ 'maxA' ] = max( diff[ classId ] [ 'maxA' ], 
                abs( lA.rect.A - match.rect.A ) )
            diff[ classId ] [ 'maxS' ] = max( diff[ classId ] [ 'maxS' ], 
                abs( lA.score - match.score ) )
    return diff
