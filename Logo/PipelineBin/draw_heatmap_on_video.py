#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineThread.VideoHeatmapThread import VideoHeatmapThread

if __name__ == '__main__':
  if len(sys.argv) < 6:
    print 'Usage %s <config.yaml> <videoFileName> <jsonFolder> <numpyFolder> <videoOutputFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  jsonFolder = sys.argv[3]
  numpyFolder = sys.argv[4]
  videoOutputFolder = sys.argv[5]

  videoHeatmapThread = VideoHeatmapThread(configFileName, \
    videoFileName, jsonFolder, numpyFolder, videoOutputFolder)
  videoHeatmapThread.run()
