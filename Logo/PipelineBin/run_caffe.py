#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineThread.CaffeThread import CaffeThread

if __name__ == '__main__':
  if len(sys.argv) < 5:
    print 'Usage %s <config.yaml> <videoFileName> <leveldbFolder> <jsonFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  leveldbFolder = sys.argv[3]
  jsonFolder = sys.argv[4]

  caffeThread = CaffeThread(configFileName, videoFileName, leveldbFolder, jsonFolder)
  caffeThread.run()
