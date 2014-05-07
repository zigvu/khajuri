from yapsy.IPlugin import IPlugin
import logging
from Heartbeat import Heartbeat
class ProcessVideo(IPlugin):
    def run( self, params ):
       videoFilePath = params.get( 'video.file.path' )
       activityWorker = params.get( 'activity.worker' )
       dsg = params.get( 'dsg' )
       if videoFilePath and activityWorker and dsg:
          self.evalVideo( activityWorker, dsg, videoFilePath )
       else:
          raise Exception( 'Not enough arguments for ProcessVideo' )

    def evalVideo( self, activityWorker, dsg, videoFilePath ):
      try:
        logging.info( 'Starting Video Evaluation' )
        activityWorker.heartbeat()
        dsg.runVidPipe( str( videoFilePath ), Heartbeat( activityWorker ) )
        logging.info( 'Video evaluation completed successfully.' )
      except Exception, e:
        logging.info( 'Exception during Video Evaluation %s' % e )
        activityWorker.fail( reason=" Exception Occurred" )
        raise Exception( 'Exception during Video Evaluation' )
