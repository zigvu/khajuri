#!/usr/bin/python
import sys
from PostProcessingConfig import PostProcessConfig
from Predictor import Predictor
# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/Controller' % baseScriptDir )
sys.path.append( '%s/VideoReader'% baseScriptDir  )
for dir in glob.glob( '%s/plugins/*' % baseScriptDir  ):
  sys.path.append( dir )

if __name__ == '__main__':
  if len( sys.argv ) < 4:
    print 'Usage %s <config.yaml> <input.dir> <output.dir>' % sys.argv[ 0 ]
  else:
    postProcessConfig = PostProcessConfig( sys.argv[ 1 ], sys.argv[ 2 ], sys.argv[ 3 ] )
    postProcessor = Predictor( postProcessConfig )
    postProcessor.run()
    postProcessor.saveResults()
