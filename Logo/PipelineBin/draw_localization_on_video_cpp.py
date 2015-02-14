#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineThread.VideoLocalizationCppThread import VideoLocalizationCppThread

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print 'Usage %s <config.yaml> <videoFileName>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]

  videoLocalizationThread = VideoLocalizationCppThread(configFileName,videoFileName)
  videoLocalizationThread.run()
