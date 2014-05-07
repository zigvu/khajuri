from yapsy.IPlugin import IPlugin
import logging, os, yaml, glob
from YouTubeDownloader import downloadYoutubeVideo
import S3Client

config = yaml.load( open( "swf.yaml", "r" ) )
class UploadResults(IPlugin):
    def run( self, params ):
       videoDir = params.get( 'video.dir.path' )
       activityWorker = params.get( 'activity.worker' )
       videoId = params[ config[ 'videoIdKey' ] ]
       if videoDir and activityWorker:
          self.uploadResults( videoId, videoDir, activityWorker )
       else:
          raise Exception( 'Not enough arguments for %s' % self )

    def uploadResults( self, videoId, videoDir, activityWorker ):
      try:
        activityWorker.heartbeat()
        logging.info( 'Starting Video results upload from %s...' % videoDir )
        myConn = S3Client.ZigVuS3Connection()
        for jsonFile in glob.glob( os.path.join( videoDir, "*json" ) ):
          myConn.putVideoResultsFile( videoId, config[ 'bucketname' ], jsonFile )
        activityWorker.complete( result="Video Result" )
      except Exception, e:
        logging.info( 'Exception during Results Upload %s' % e )
        activityWorker.fail( reason=" Exception Occurred during results upload " )
        raise Exception( "Exception occurred during results upload" )
