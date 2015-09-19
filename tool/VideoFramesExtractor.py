#!/usr/bin/python
import glob, sys, time
import os, tempfile, pdb
from multiprocessing import Process

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append('%s/../VideoReader' % baseScriptDir)

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader

if __name__ == '__main__':
  if len(sys.argv) < 4:
    print 'Usage %s <video.file> <frame.numbers> <output.dir> <frame.prefix (optional)>' % sys.argv[0]
    print 'frame.numbers is a file with the frame numbers separated by spaces'
    print 'frame.prefix is the string that is prefixed prior to frame number in each frame'
    sys.exit(1)
  videoFileName = sys.argv[1]
  frameNumsFile = sys.argv[2]
  outputDir = sys.argv[3]

  framePrefix = ""
  if len(sys.argv) > 4:
    framePrefix = "%s_" % sys.argv[4]

  if not os.path.exists(outputDir):
    os.makedirs(outputDir)
  f = open(frameNumsFile, "r")
  frameNums = f.read().split()
  videoFrameReader = VideoFrameReader(videoFileName)
  for frameNum in sorted( map( int, frameNums ) ):
    fileName = os.path.join(outputDir, "%s%s.png" % (framePrefix, frameNum))
    success = videoFrameReader.savePngWithFrameNumber(int(frameNum), fileName)
    if success:
      print frameNum
    else:
      print "Couldn't extract frame number %d" % frameNum
  videoFrameReader.close()
