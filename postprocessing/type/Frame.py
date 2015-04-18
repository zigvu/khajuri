import numpy as np
import logging

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

  def __str__( self ):
    return 'Frame(%s)' % ( self.localizations.items() )
