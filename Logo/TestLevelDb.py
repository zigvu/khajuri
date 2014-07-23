#!/usr/bin/python
import glob, sys, time
import os, tempfile, pdb
from multiprocessing import Process

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../VideoReader'% baseScriptDir  )

from LogoPipeline import BoundingBoxes
import VideoReader
import caffe

if __name__ == '__main__':
  if len( sys.argv ) < 5:
    print 'Usage %s <video.file> <output.dir> <model.file> <caffe.train.file>' % sys.argv[ 0 ]
    sys.exit( 1 )
  videoFileName = sys.argv[ 1 ]
  outputDir = sys.argv[ 2 ]

  # Setup
  if not os.path.exists( outputDir ):
    os.makedirs( outputDir )
  videoFrameReader = VideoReader.VideoFrameReader( 40, 40, videoFileName )
  videoFrameReader.generateFrames()
  time.sleep( 10 )
  fps = videoFrameReader.fps
  pyLevelDb = VideoReader.VideoLevelDb( os.path.join( outputDir, "level-Db" ) )
  pyLevelDb.setVideoFrameReader( videoFrameReader )

  
  # Generate a single Level Db
  frameNum = 1
  scaling = [ 1 ]
  boundingBoxes = {}
  while not videoFrameReader.eof or frameNum <= videoFrameReader.totalFrames:
    for scale in scaling:
      if not boundingBoxes.get( scale ):
        boundingBoxes[ scale ] = [ ( 0, 0, 256, 256 ) ]
      for box in boundingBoxes[ scale ]:
        pyLevelDb.savePatch( frameNum, scale, box[ 0 ], box[ 1 ], box[ 2 ], box [ 3 ] )
    frameNum += 5
  pyLevelDb.saveLevelDb()

  # TestNet to get the scores for the patches
  classes = [ "0", "1" ]
  model_file = sys.argv[ 3 ]
  pretrained_file = sys.argv[ 4 ]
  test_net = caffe.Net( model_file, pretrained_file )
  test_net.set_phase_test()
  test_net.set_mode_cpu()
  output = test_net.forward()
  probablities = output['prob']
  numOfClasses = len( classes )
  scores = {}
  for i in range( 0, output[ 'label' ].size ):
    print 'For Patch %s' % i
    for j in range( 0, numOfClasses ):
      print '  Class %s, Score %s' % ( classes[ j ], probablities.item( numOfClasses * i + j ) )
