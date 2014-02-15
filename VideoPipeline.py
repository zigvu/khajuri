#!/usr/bin/python
import glob, sys
import os

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/Controller' % baseScriptDir )
sys.path.append( '%s/VideoReader'% baseScriptDir  )
for dir in glob.glob( '%s/plugins/*' % baseScriptDir  ):
	sys.path.append( dir )

import Config
from Frame import FrameGroup
from Plugin import PluginGroup, BlankDetection, BlurDetection
from Result import ResultGroup
from DetectionStrand import DetectionStrand, DetectionStrandGroup

def processVideo( configPath, videoFilePath ):
	config = Config.Config( configPath )
	videoFileName = videoFilePath
	dsg = DetectionStrandGroup( videoFileName, config )
	dsg.runVidPipe()

if __name__ == '__main__':
	if len( sys.argv ) < 3:
		print 'Usage %s <config.yaml> <video.file>' % sys.argv[ 0 ]
        else:
		processVideo( sys.argv[ 1 ], sys.argv[ 2 ] )
