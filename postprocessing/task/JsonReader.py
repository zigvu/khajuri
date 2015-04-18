import logging, json

from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

class JsonReader( Task ):
  def __call__( self, obj ):
    fileName = obj
    frame = Frame( self.config.ci_allClassIds, 543, [ 'fc8', 'prob' ] )
    logging.info( 'Reading frameInfo from %s' % fileName )
    jsonObj = json.load( open( fileName, 'r' ) )
    frame.frameDisplayTime = jsonObj[ 'frame_time' ]
    frame.frameNumber = jsonObj[ 'frame_number' ]

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

    # Patch Scores
    for classId, scores in jsonObj[ 'scores' ].iteritems():
      for scoreType, scores in scores.iteritems():
        frame.addScore( classId, self.config.ci_scoreTypes[ scoreType ], 0, scores )

    return ( frame, jsonObj[ 'scores' ].keys() )
