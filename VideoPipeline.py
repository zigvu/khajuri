#!/usr/bin/python
import glob, sys
import os, tempfile, pdb

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/Controller' % baseScriptDir )
sys.path.append( '%s/VideoReader'% baseScriptDir  )
for dir in glob.glob( '%s/plugins/*' % baseScriptDir  ):
	sys.path.append( dir )

from Controller.Config import Config
from Controller.Frame import FrameGroup
from Controller.Result import ResultGroup
from Controller.DetectionStrand import DetectionStrand, DetectionStrandGroup

def processVideo( configPath, videoFilePath ):
	config = Config.Config( configPath )
	dsg = DetectionStrandGroup( videoFilePath, config )
	dsg.runVidPipe()

if __name__ == '__main__':
	if len( sys.argv ) < 3:
		print 'Usage %s <config.yaml> <video.file>' % sys.argv[ 0 ]
        else:
		processVideo( sys.argv[ 1 ], sys.argv[ 2 ] )
