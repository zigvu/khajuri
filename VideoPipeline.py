#!/usr/bin/python
import glob, sys

# Add files to path
sys.path.append( './Controller' )
sys.path.append( './VideoReader' )
for dir in glob.glob( './plugins/*' ):
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
