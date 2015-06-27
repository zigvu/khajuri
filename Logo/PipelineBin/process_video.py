#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append('%s/../../VideoReader' % baseScriptDir)

from Logo.PipelineThread.VideoProcessThread import VideoProcessThread

description = \
"""
This script will run a video through caffe and post-processing pipeline
"""

def main():
  if len(sys.argv) < 8:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    print description
    sys.exit(1)

  configFileName = sys.argv[1]
  videoProcessThread = VideoProcessThread(configFileName)
  videoProcessThread.run()


if __name__ == '__main__':
  main()
