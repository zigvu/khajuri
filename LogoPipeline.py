#!/usr/bin/python
import glob, sys
import os

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/Controller' % baseScriptDir )
sys.path.append( '%s/VideoReader'% baseScriptDir  )
for dir in glob.glob( '%s/plugins/*' % baseScriptDir  ):
  sys.path.append( dir )

import Logo.LogoPipeline 
if __name__ == '__main__':
  if len( sys.argv ) < 4:
    print 'Usage %s <config.yaml> <video.file> <output.dir>' % sys.argv[ 0 ]
  else:
    logoPipeLine = Logo.LogoPipeline.LogoPipeline()
    logoPipeLine.run()

