#!/usr/bin/python
import glob, sys
import os, tempfile, pdb, time
from multiprocessing import Process

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/VideoReader'% baseScriptDir  )

import VideoReader

if __name__ == '__main__':
  if len( sys.argv ) < 5:
    print 'Usage %s <video.file> <frame.times> <numOfFrames> <output.dir>' % sys.argv[ 0 ]
    print 'frame.times is a file with the frame times separated by spaces. Times are expected in seconds.'
    sys.exit( 1 )
  videoFileName = sys.argv[ 1 ]
  frameTimesFile = sys.argv[ 2 ]
  numOfFrames = int( sys.argv[ 3 ] )
  outputDir = sys.argv[ 4 ]
  if not os.path.exists( outputDir ):
    os.makedirs( outputDir )
  f = open( frameTimesFile, "r" )
  frameTimes = f.read().split()
  frameTimes = map( int, frameTimes )
  videoFrameReader = VideoReader.VideoFrameReader( 40, 40, videoFileName )
  videoFrameReader.generateFrames()
  time.sleep( 1 )
  fps = videoFrameReader.fps
  frameNums = []
  for second in frameTimes:
    expectedFrame = int( fps * float( second ) )
    for frame in range( expectedFrame - numOfFrames/2, expectedFrame + ( numOfFrames/2 ) + 1 ):
      frameNums.append( frame )
  outputDirId = os.path.basename( outputDir ).split('.')[0]
  for frameNum in sorted( set( frameNums ) ):
    fileName = os.path.join( outputDir, "%s_frame_%s.png" % ( outputDirId, frameNum ) )
    print 'Saving Frame: %s' % fileName
    videoFrameReader.savePngWithFrameNumber(int(frameNum), fileName)

  print "Done"
