import json, logging

from hdf5Storage.type.FrameData import FrameData
from hdf5Storage.infra.VideoDataWriter import VideoDataWriter

from messaging.infra.Pickler import Pickler
from messaging.type.Headers import Headers

class VideoDataHandler( object ):
  def __init__( self, kheerRpcClient ):
    self.kheerRpcClient = kheerRpcClient
    # hash format:
    # {chia_version_id: {video_id: hdf5Storage.infra.VideoDataWriter}}
    self.videoDataWriters = {}

  def startNewVideoStorage( self, videoId, chiaVersionId, config ):
    logging.info( "Start data import for video_id %d and chia_version_id %d" % ( videoId, chiaVersionId ) )
    if not chiaVersionId in self.videoDataWriters.keys():
      self.videoDataWriters[ chiaVersionId ] = {}
    if videoId in self.videoDataWriters[ chiaVersionId ].keys():
      raise RuntimeError( "Data import for video_id %d and chia_version_id %d already in progress" % \
        ( videoId, chiaVersionId )
      )
    # create new writer
    self.videoDataWriters[ chiaVersionId ][ videoId ] = VideoDataWriter( config, videoId, chiaVersionId )
    # inform kheer of incoming data
    message = {}
    headers = Headers.videoStorageStart( videoId, chiaVersionId )
    response = json.loads( self.kheerRpcClient.call( headers, json.dumps( message ) ) )
    # TODO: error check

  def endExistingVideoStorage( self, videoId, chiaVersionId ):
    logging.info( "End data import for video_id %d and chia_version_id %d" % ( videoId, chiaVersionId ) )
    self.videoDataWriters[ chiaVersionId ][ videoId ].close()
    self.videoDataWriters[ chiaVersionId ].pop( videoId )
    # inform kheer of ending data
    message = {}
    headers = Headers.videoStorageEnd( videoId, chiaVersionId )
    response = json.loads( self.kheerRpcClient.call( headers, json.dumps( message ) ) )
    # TODO: error check

  def addToExistingVideoStorage( self, videoId, chiaVersionId, frameData ):
    # push data to HDFS
    self.videoDataWriters[ chiaVersionId ][ videoId ].addFrameData( frameData )
    # push data to kheer
    message = frameData.getLocalizationArr()
    headers = Headers.videoStorageSave( videoId, chiaVersionId )
    response = json.loads( self.kheerRpcClient.call( headers, json.dumps( message ) ) )
    # TODO: error check

  def handle( self, headers, message ):
    videoId = Headers.getPropsVideoId( headers )
    chiaVersionId = Headers.getPropsChiaVersionId( headers )

    if Headers.isVideoStorageStart( headers ):
      self.startNewVideoStorage( videoId, chiaVersionId, message )
    elif Headers.isVideoStorageEnd( headers ):
      self.endExistingVideoStorage( videoId, chiaVersionId )
    elif Headers.isVideoStorageSave( headers ):
      self.addToExistingVideoStorage( videoId, chiaVersionId, message )
    else:
      raise RuntimeError( "Unknown task headers" )

    # TODO: error check
    responseHeaders = Headers.statusSuccess()
    responseMessage = {
      'video_id': videoId,
      'chia_version_id': chiaVersionId
    }
    return responseHeaders, json.dumps( responseMessage )

  # input to this function is a pickled object, output is JSON
  def __call__( self, headers, message ):
    return self.handle( headers, Pickler.unpickle( message ) )
