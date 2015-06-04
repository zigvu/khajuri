import json, logging

from messaging.type.Headers import Headers
from hdf5Storage.infra.VideoDataReader import VideoDataReader

class HeatmapDataHandler( object ):
  def __init__( self ):
    pass

  def handle( self, headers, heatmapRequest ):
    # request syntax should match in
    # kheer/services/messaging_services/heatmap_data.rb
    videoId = int( heatmapRequest[ 'video_id' ] )
    chiaVersionid = int( heatmapRequest[ 'chia_version_id' ] )
    frameNumber = int( heatmapRequest[ 'frame_number' ] )
    scale = float( heatmapRequest[ 'scale'] )
    chiaClassId = str( heatmapRequest[ 'chia_class_id' ] )

    with open( '/home/evan/Vision/temp/RabbitMQ/data/cell_values.json' ) as f:
      data = json.load( f )

      responseHeaders = Headers.statusSuccess()
      responseMessage = json.dumps( data )
      logging.info( "Heatmap supplied for: VideoId: %d, ChiaVersionId: %d, FrameNumber: %d, Scale: %f, ChiaClassId: %s" % 
        ( videoId, chiaVersionid, frameNumber, scale, chiaClassId) )

      return responseHeaders, responseMessage

  # both input/output are JSON
  def __call__( self, headers, message ):
    return self.handle( headers, json.loads( message ) )

