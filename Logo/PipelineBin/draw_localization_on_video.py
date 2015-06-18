#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append('%s/../../VideoReader' % baseScriptDir)

from Logo.PipelineThread.VideoLocalizationThread import VideoLocalizationThread

description = \
"""
This script will draw localization on a video
"""

def main():
  if len(sys.argv) < 5:
    print 'Usage %s ' % sys.argv[0] + \
      '<config.yaml> <videoFileName> <jsonFolder> <videoOutputFolder>'
    print description
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  jsonFolder = sys.argv[3]
  videoOutputFolder = sys.argv[4]

  videoLocalizationThread = VideoLocalizationThread(
      configFileName, videoFileName, jsonFolder, videoOutputFolder)
  videoLocalizationThread.run()


if __name__ == '__main__':
  main()
