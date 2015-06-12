#!/usr/bin/python

import sys, os, glob

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineThread.VideoProcessThread import VideoProcessThread

def main():
  if len(sys.argv) < 8:
    print 'Usage %s <config.yaml> <videoFileName> <baseDbFolder> <jsonFolder> <numpyFolder> <videoId> <chiaVersionId>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  baseDbFolder = sys.argv[3]
  jsonFolder = sys.argv[4]
  numpyFolder = sys.argv[5]
  videoId = int(sys.argv[6])
  chiaVersionId = int(sys.argv[7])
  videoProcessThread = VideoProcessThread(configFileName, videoFileName, \
    baseDbFolder, jsonFolder, numpyFolder, videoId, chiaVersionId)
  videoProcessThread.run()

if __name__ == '__main__':
  main()

