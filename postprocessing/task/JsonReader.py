import logging, json, os

from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

class JsonReader( Task ):
  def getVideoId( self, jsonFileName ):
    baseName = os.path.basename( jsonFileName )
    return baseName.split( '_' )[0]

  def __call__( self, obj ):
    fileName = obj
    logging.info( 'Reading frameInfo from %s' % fileName )
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
        frame.addLocalization( int( classId ), l )


    return ( frame, jsonObj[ 'scores' ].keys() )
