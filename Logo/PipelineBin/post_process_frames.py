#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineThread.PostProcessThread import PostProcessThread

if __name__ == '__main__':
  if len(sys.argv) < 4:
    print 'Usage %s <config.yaml> <videoFileName> <jsonFolder> <outputFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  jsonFolder = sys.argv[3]
  outputFolder = sys.argv[4]

  

  postProcessThread = PostProcessThread(configFileName, videoFileName, jsonFolder, outputFolder)
  postProcessThread.run()

