#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineThread.VideoLocalizationThread import VideoLocalizationThread

if __name__ == '__main__':
  if len(sys.argv) < 5:
    print 'Usage %s <config.yaml> <videoFileName> <jsonFolder> <videoOutputFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  jsonFolder = sys.argv[3]
  videoOutputFolder = sys.argv[4]

  videoLocalizationThread = VideoLocalizationThread(configFileName, \
  	videoFileName, jsonFolder, videoOutputFolder)
  videoLocalizationThread.run()
