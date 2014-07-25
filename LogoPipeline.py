#!/usr/bin/python
import glob, sys
import os

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/Controller' % baseScriptDir )
sys.path.append( '%s/VideoReader'% baseScriptDir  )
for dir in glob.glob( '%s/plugins/*' % baseScriptDir  ):
  sys.path.append( dir )

import Logo.Pipeline 
if __name__ == '__main__':
  if len(sys.argv) < 4:
    print 'Usage %s <config.yaml> <videoFileName> <outputDir>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  outputDir = sys.argv[3]

  pipeline = Logo.Pipeline.Pipeline(configFileName, videoFileName, outputDir)
  pipeline.run()
