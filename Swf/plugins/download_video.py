from yapsy.IPlugin import IPlugin
import logging, os, yaml, json
from YouTubeDownloader import downloadYoutubeVideo
import FFProbe

config = yaml.load( open( "swf.yaml", "r" ) )
class DownloadVideo(IPlugin):
    def run( self, params ):
       youtubeUrl = params.get( config[ 'videoUrlKey' ] )
       activityWorker = params.get( 'activity.worker' )
       if youtubeUrl and activityWorker:
          params[ 'video.file.path' ], params[ 'video.dir.path' ]  = self.getVideo( youtubeUrl, activityWorker )
       else:
          raise Exception( 'Not enough arguments for %s' % self )

    def getVideo( self, youtubeUrl, activityWorker ):
      try:
        logging.info( 'Starting Video download from URL %s...' % youtubeUrl )
        activityWorker.heartbeat()
        videoJson, videoFile = downloadYoutubeVideo( youtubeUrl )
        videoDir = os.path.join( os.getcwd(), videoFile.split('.')[0] )
        videoDescription = FFProbe.probeVideoFile( videoFile, videoJson )
        inspectOutputFile = open( os.path.join( videoDir, "inspect.json" ), "w" )
        json.dump( videoDescription, inspectOutputFile, indent=2 )
        inspectOutputFile.close()
        inspectOutputFile.close()
        if not os.path.exists( videoDir ):
           os.makedirs( videoDir )
        os.system( "mv %s %s" % ( videoFile, videoDir ) )
        videoFile = os.path.join( videoDir, videoFile )
        logging.info( 'Done with Video Download, saving at: %s ' % videoFile )
        return videoFile, videoDir
      except Exception, e:
        logging.info( 'Exception during Video Download %s' % e )
        activityWorker.fail( reason=" Exception Occurred" )
