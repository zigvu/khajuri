#!/usr/bin/python
import glob, sys
import os, tempfile, pdb
from multiprocessing import Process
import yaml, json

class MyMock( object ):
  def heartbeat( self ):
    pass

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/Controller' % baseScriptDir )
sys.path.append( '%s/VideoReader'% baseScriptDir  )
for dir in glob.glob( '%s/plugins/*' % baseScriptDir  ):
  sys.path.append( dir )

def createDirIfNotExists( dirName ):
  if not os.path.exists( dirName ):
    os.makedirs( dirName )

import VideoReader

class BoundingBoxes( object ):
  def __init__( self, config, width, height, scale ):
    print 'Creating Bounding Boxes'
    self.config = config
    self.width = width * scale
    self.height = height * scale

  def getBoundingBoxes( self ):
    boundingBoxes = []
    xstepSize  = self.config[ 'sliding_window' ] [ 'x_stride' ]
    ystepSize  = self.config[ 'sliding_window' ] [ 'y_stride' ]
    patchSizeWidth = self.config[ 'output_width' ]
    patchSizeHeight = self.config[ 'output_height' ]
    x = 0
    while x + patchSizeWidth <= self.width:
      y = 0
      while y + patchSizeHeight <= self.height:
        boundingBoxes.append( ( x, y, patchSizeWidth, patchSizeHeight ) )
        y += ystepSize
      if y < self.height:
        boundingBoxes.append(( x, int( self.height - patchSizeHeight), patchSizeWidth, patchSizeHeight ) )
      x += xstepSize

    if x < self.width:
      y = 0
      while y + patchSizeHeight <= self.height:
        boundingBoxes.append( ( int( self.width - patchSizeWidth ), y, patchSizeWidth, patchSizeHeight ) )
        y += ystepSize

    if x < self.width and y < self.height:
      boundingBoxes.append( ( int( self.width - patchSizeWidth ), 
                              int( self.height - patchSizeHeight ), 
                              patchSizeWidth, patchSizeHeight ) )

    return boundingBoxes


class Annotations( object ):
  def __init__( self, videoId, frameId, scaling ):
    self.videoId = videoId
    self.frameId = frameId
    self.myDict = {}
    self.myDict[ 'annotation_filename' ] = '%s_frame_%s.json' % ( videoId, frameId )
    self.myDict[ 'frame_filename' ] = '%s_frame_%s.png' % ( videoId, frameId )
    self.myDict[ 'frame_number' ] = frameId
    self.myDict[ 'scales' ] = []
    self.scales = {}
    for scale in scaling:
      self.scales[ scale ]  = []

  def addBoundingBox( self, scale, patchNum, x, y, width, height ):
    self.scales[ scale ].append( 
        { 'patch_filename' : '%s_frame_%s_scl_%s_idx_%s.png' % ( self.videoId,
                                                                 self.frameId,
                                                                 scale,
                                                                 patchNum ),
           'patch' : {
             'x' : x,
             'y' : y,
             'width' : width,
             'height' : height,
             }
           } )


  def dump( self, fileName ):
    self.myDict[ "scales" ] = []
    for key, value in self.scales.iteritems():
      self.myDict[ 'scales' ].append( {
        'scale': key,
        'patches': value
        } )
    with open( fileName, "w" ) as f:
      json.dump( self.myDict, f, indent=2 )

if __name__ == '__main__':
  if len( sys.argv ) < 3:
    print 'Usage %s <config.yaml> <video.file>' % sys.argv[ 0 ]
  else:
    f = open( sys.argv[ 1 ] )
    config = yaml.safe_load(f)
    f.close()
    videoFileName = sys.argv[ 2 ]
    videoFrameReader = VideoReader.VideoFrameReader( 40, 40, videoFileName )
    videoFrameReader.generateFrames()
    import time
    time.sleep( 1 )
    fps = videoFrameReader.fps

    # Part of Config.yaml file
    outputFramesDir = os.path.join( "output", "frames" )
    outputPatchesDir = os.path.join( "output", config[ 'sliding_window' ][ 'folders' ]["patch_output" ] )
    outputJsonDir = os.path.join( "output", config[ 'sliding_window' ][ 'folders' ]["annotation_output"] )
    frameStep = config[ 'sliding_window' ] [ 'frame_density' ]
    scaling = config[ 'sliding_window' ][ 'scaling' ]

    # Setup
    videoName = os.path.basename( videoFileName )
    videoId = videoName.split('.')[0]
    createDirIfNotExists( outputFramesDir )
    createDirIfNotExists( outputPatchesDir )
    createDirIfNotExists( outputJsonDir )

    # Get the bouding boxes
    boundingBoxes = {}
    frameNum = 1
    while not videoFrameReader.eof or frameNum <= videoFrameReader.totalFrames:
      fileName = os.path.join( outputFramesDir, "%s_frame_%s.png" % ( videoId, frameNum ) )
      # print 'Saving Frame: %s' % fileName
      frame = videoFrameReader.getFrameWithFrameNumber( int( frameNum ) )
      while not frame:
        frame = videoFrameReader.getFrameWithFrameNumber( int( frameNum ) )
      annotations = Annotations( videoId, frameNum, scaling )
      for scale in scaling:
        if not boundingBoxes.get( scale ):
          boundingBoxes[ scale ] = BoundingBoxes( config, frame.width, frame.height, scale ).getBoundingBoxes()
        videoFrameReader.savePngWithFrameNumber(int(frameNum), fileName)
        patchNum = 0
        for box in boundingBoxes[ scale ]:
          patchFileName = os.path.join( outputPatchesDir, "%s_frame_%s_scl_%s_idx_%s.png" % ( videoId, int( frameNum ), scale,  patchNum ) )
          # print 'Saving Patch: %s' % patchFileName
          videoFrameReader.patchFromFrameNumber( frameNum, patchFileName, scale, box[ 0 ], box[ 1 ], box[ 2 ], box [ 3 ] )
          annotations.addBoundingBox( scale, patchNum, box[ 0 ], box[ 1 ], box[ 2 ], box[ 3 ] )
          patchNum += 1
      annotations.dump( 
          os.path.join( outputJsonDir, '%s_frame_%s.json'  % ( videoId, frameNum ) ) )
      frameNum += frameStep
