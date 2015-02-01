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
    print 'Usage %s <video.file> <frame.numbers> <output.dir>' % sys.argv[0]
    print 'frame.numbers is a file with the frame numbers separated by spaces'
    sys.exit(1)
  videoFileName = sys.argv[1]
  frameNumsFile = sys.argv[2]
  outputDir = sys.argv[3]
  if not os.path.exists(outputDir):
    os.makedirs(outputDir)
  f = open(frameNumsFile, "r")
  frameNums = f.read().split()
  videoFrameReader = VideoFrameReader(videoFileName)
  outputDirId = os.path.basename(outputDir)
  for frameNum in frameNums:
    fileName = os.path.join(
        outputDir, "%s_frame_%s.png" % (outputDirId, frameNum))
    videoFrameReader.savePngWithFrameNumber(int(frameNum), fileName)
  videoFrameReader.close()
