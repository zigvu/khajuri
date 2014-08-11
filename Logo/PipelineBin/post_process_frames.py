#!/usr/bin/python

import sys, os, glob, time

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineThread.PostProcessThread import PostProcessThread

if __name__ == '__main__':
  if len(sys.argv) < 4:
    print 'Usage %s <config.yaml> <jsonFolder> <numpyFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  startTime = time.time()
  configFileName = sys.argv[1]
  jsonFolder = sys.argv[2]
  numpyFolder = sys.argv[3]

  postProcessThread = PostProcessThread(configFileName, jsonFolder, numpyFolder)
  postProcessThread.run()
  endTime = time.time()
  print 'It took %s %s seconds to complete' % ( sys.argv[0], endTime - startTime )
