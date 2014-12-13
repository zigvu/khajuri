#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineThread.VideoProcessThread import VideoProcessThread

if __name__ == '__main__':
  if len(sys.argv) < 6:
    print 'Usage %s <config.yaml> <videoFileName> <baseDbFolder> <jsonFolder> <numpyFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  baseDbFolder = sys.argv[3]
  jsonFolder = sys.argv[4]
  numpyFolder = sys.argv[5]
  videoProcessThread = VideoProcessThread(configFileName, videoFileName, baseDbFolder, jsonFolder, numpyFolder)
  videoProcessThread.run()
