import logging, json, os

from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

class CompareFrame( Task ):

  def compareRect( self, r1, r2 ):
    pass

  def compareLocalization( self, l1, l2 ):
    pass

  def score( self, s1, s2 ):
    pass

  def __call__( self, obj ):
    fileNames, formats = obj
    logging.info( 'Comparing files %s with formats %s' % ( fileNames, formats ) )
    if not self.config.videoId:
      self.config.videoId = self.getVideoId( fileName )
    jsonObj = json.load( open( fileName, 'r' ) )
    frame = Frame( self.config.ci_allClassIds, 543, self.config.ci_scoreTypes.keys() )
    frame.frameDisplayTime = jsonObj[ 'frame_time' ]
    frame.frameNumber = jsonObj[ 'frame_number' ]

    # Patch Scores
    for classId, scores in jsonObj[ 'scores' ].iteritems():
      for scoreType, scores in scores.iteritems():
        frame.addScore( classId, self.config.ci_scoreTypes[ scoreType ], 0, scores )

    # Localizations
    for classId, localizationList in jsonObj[ 'localizations' ].iteritems():
      for l in localizationList:
        score = l[ 'score' ]
        scale = l[ 'scale' ]
        bbox = l[ 'bbox' ]
        zDist = l[ 'zdist_thresh' ]
        r = Rect( bbox[ 'x' ], bbox[ 'y' ], bbox[ 'width' ], bbox[ 'height' ] )
        l = Localization( zDist, classId, r, score, scale )
        logging.info( 'Adding localization %s' % l )
        frame.addLocalization( classId, l )


    return ( frame, jsonObj[ 'scores' ].keys() )
