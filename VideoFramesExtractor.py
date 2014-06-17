#!/usr/bin/python
import glob, sys, time
import os, tempfile, pdb
from multiprocessing import Process

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/VideoReader'% baseScriptDir  )

import VideoReader

if __name__ == '__main__':
  if len( sys.argv ) < 4:
    print 'Usage %s <video.file> <frame.numbers> <output.dir>' % sys.argv[ 0 ]
    print 'frame.numbers is a file with the frame numbers separated by spaces'
    sys.exit( 1 )
  videoFileName = sys.argv[ 1 ]
  frameNumsFile = sys.argv[ 2 ]
  outputDir = sys.argv[ 3 ]
  if not os.path.exists( outputDir ):
    os.makedirs( outputDir )
  f = open( frameNumsFile, "r" )
  frameNums = f.read().split()
  videoFrameReader = VideoReader.VideoFrameReader( 40, 40, videoFileName )
  videoFrameReader.generateFrames()
  fps = videoFrameReader.fps
  for frameNum in sorted( frameNums ):
    fileName = os.path.join( outputDir, "%s.png" % frameNum )
    videoFrameReader.savePngWithFrameNumber(int(frameNum), fileName)
    if videoFrameReader.eof:
      break;

  while not videoFrameReader.eof:
    videoFrameReader.seekToFrameWithFrameNumber( int( frameNum ) )
    frameNum = int( frameNum ) + 100
  videoFrameReader.waitForEOF()
