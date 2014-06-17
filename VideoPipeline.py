#!/usr/bin/python
import glob, sys
import os, tempfile, pdb
from multiprocessing import Process

class MyMock( object ):
  def heartbeat( self ):
    pass

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/Controller' % baseScriptDir )
sys.path.append( '%s/VideoReader'% baseScriptDir  )
for dir in glob.glob( '%s/plugins/*' % baseScriptDir  ):
  sys.path.append( dir )

from Controller.Config import Config
from Controller.PluginGroup import PluginGroup
from Controller.Frame import FrameGroup
from Controller.Result import ResultGroup
from Controller.DetectionStrand import DetectionStrand, DetectionStrandGroup
from plugins.model_eval.ModelDetectionHelper import ModelDetection

def processVideo( dsg, videoFilePath ):
  dsg.runVidPipe( videoFilePath, MyMock() )

if __name__ == '__main__':
  if len( sys.argv ) < 3:
    print 'Usage %s <config.yaml> <video.file>' % sys.argv[ 0 ]
  else:
    config = Config( sys.argv[ 1 ] )
    os.environ[ "VIDEO_FRAME_WIDTH" ] = "%s" % config.getFrameWidth()
    os.environ[ "VIDEO_FRAME_HEIGHT" ] = "%s" % config.getFrameHeight()
    dsg = DetectionStrandGroup( config )
    pendingProcess = []
    for plugin in config.getPluginClassNames():
      if plugin.startswith( "Model" ):
        modelConfig = config.getPluginConfig( plugin )
        modelDet = ModelDetection(modelConfig)
    for video in range( 2, len( sys.argv ) ):
      p = Process(target=processVideo, args=( dsg, sys.argv[ video ] ))
      p.start()
      pendingProcess.append( p )

    for p in pendingProcess:
      p.join()
