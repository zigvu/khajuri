import json, logging
import numpy as np

from Logo.PipelineMath.PixelMap import PixelMap

from messaging.type.Headers import Headers
from hdf5Storage.infra.VideoDataReader import VideoDataReader

class HeatmapDataHandler( object ):
  def __init__( self, config ):
    self.config = config

  def handle( self, headers, heatmapRequest ):
    # request syntax should match in
    # kheer/services/messaging_services/heatmap_data.rb
    videoId = int( heatmapRequest[ 'video_id' ] )
    chiaVersionId = int( heatmapRequest[ 'chia_version_id' ] )
    frameNumber = int( heatmapRequest[ 'frame_number' ] )
    scale = float( heatmapRequest[ 'scale'] )
    chiaClassId = str( heatmapRequest[ 'chia_class_id' ] )

    responseHeaders = None
    responseMessage = None

    try:
      # construct PixelMap
      pixelMap = PixelMap( self.config.allCellBoundariesDict, scale )
      with VideoDataReader( self.config, videoId, chiaVersionId ) as vdr:
        frameData = vdr.getFrameData( frameNumber )
        patchScores = frameData.scores[ :, chiaClassId ]
        pixelMap.addScore_max( patchScores )
        # javascript expects int values between [0,100] inclusive
        cellValues = np.rint(pixelMap.cellValues * 100).tolist()

        data = { 'scores': cellValues }

        message = "Heatmap supplied for: VideoId: %d, ChiaVersionId: %d, FrameNumber: %d, Scale: %f, ChiaClassId: %s" % \
          ( videoId, chiaVersionId, frameNumber, scale, chiaClassId )
        logging.info( message )
        responseHeaders = Headers.statusSuccess()
        responseMessage = json.dumps( data )
    except Exception, e:
      message = "No heatmap found for: VideoId: %d, ChiaVersionId: %d, FrameNumber: %d, Scale: %f, ChiaClassId: %s" % \
        ( videoId, chiaVersionId, frameNumber, scale, chiaClassId )
      logging.error( message )
      responseHeaders = Headers.statusFailure( message )
      responseMessage = json.dumps( { 'scores': [] } )

    return responseHeaders, responseMessage

  # both input/output are JSON
  def __call__( self, headers, message ):
    return self.handle( headers, json.loads( message ) )

