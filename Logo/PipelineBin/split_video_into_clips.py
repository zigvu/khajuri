#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append('%s/../../VideoReader' % baseScriptDir)

from Logo.PipelineThread.VideoSplitterThread import VideoSplitterThread

description = \
"""
This script will split video into clips for use with kheer and also
embed any required frame number tracking pixels.
"""

def main():
  if len(sys.argv) < 4:
    print 'Usage %s ' % sys.argv[0] + \
        '<config.yaml> <videoFileName> <clipsOutputFolder>'
    print description
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  clipsOutputFolder = sys.argv[3]

  videoSplitterThread = VideoSplitterThread(
      configFileName, videoFileName, clipsOutputFolder)
  videoSplitterThread.run()


if __name__ == '__main__':
  main()
