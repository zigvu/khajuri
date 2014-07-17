#!/usr/bin/python
import glob, sys
import os, tempfile, pdb
from multiprocessing import Process
import yaml, json
from collections import OrderedDict
from Queue import Queue
from MultiProcessFramePostProcessor import MultiProcessFramePostProcessor
from RemovePatch import RemovePatch


def createDirIfNotExists( dirName ):
  if not os.path.exists( dirName ):
    os.makedirs( dirName )

import VideoReader
class BoundingBoxes( object ):
  def __init__( self, config, width, height, scale ):
    self.config = config
    self.width = width * scale
    self.height = height * scale

  def getBoundingBoxes( self ):
    boundingBoxes = []
    xstepSize  = self.config[ 'sliding_window' ] [ 'x_stride' ]
    ystepSize  = self.config[ 'sliding_window' ] [ 'y_stride' ]
    patchSizeWidth = self.config[ 'sliding_window' ][ 'output_width' ]
    patchSizeHeight = self.config[ 'sliding_window' ][ 'output_height' ]
    x = 0
    while x + patchSizeWidth <= self.width:
      y = 0
      while y + patchSizeHeight <= self.height:
        boundingBoxes.append( ( x, y, patchSizeWidth, patchSizeHeight ) )
        y += ystepSize
      if y - ystepSize + patchSizeHeight != self.height:
        boundingBoxes.append(( x, int( self.height - patchSizeHeight), patchSizeWidth, patchSizeHeight ) )
      x += xstepSize

    if x - xstepSize + patchSizeWidth != self.width:
      y = 0
      while y + patchSizeHeight <= self.height:
        boundingBoxes.append( ( int( self.width - patchSizeWidth ), y, patchSizeWidth, patchSizeHeight ) )
        y += ystepSize

    if x - xstepSize + patchSizeWidth != self.width\
        and y - ystepSize + patchSizeHeight != self.height:
      boundingBoxes.append( ( int( self.width - patchSizeWidth ), 
                              int( self.height - patchSizeHeight ), 
                              patchSizeWidth, patchSizeHeight ) )

    return boundingBoxes


class AnnotationsReader( object ):
  def __init__( self, fileName ):
    self.myDict = json.load( open( fileName, "r" ) )
    self.scalingFactors = [ obj['scale'] for obj in self.myDict[ 'scales' ] ]

  def getAnnotationFileName( self ):
    return self.myDict[ 'annotation_filename' ]

  def getFrameFileName( self ):
    return self.myDict[ 'frame_filename' ]

  def getFrameNumber( self ):
    return self.myDict[ 'frame_number' ]

  def getScalingFactors( self ):
    return self.scalingFactors

  def getPatches( self, scale ):
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        return obj[ 'patches' ]

  def getPatchFileNames( self, scale ):
    fileNames = []
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        for patch in obj['patches']:
          fileNames.append( patch[ 'patch_filename' ] )
    return fileNames

  def getBoundingBoxes( self, scale ):
    boxes = []
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        for patch in obj['patches']:
          boxes.append( patch[ 'patch' ] )
    return boxes

  def getClassIds( self ):
    return self.myDict['scales'][0]['patches'][0]['scores'].keys()

  def getScoreForPatchIdAtScale( self, patchId, classId, scale ):
    return self.myDict['scales'][ self.scalingFactors.index( scale ) ]['patches']\
        [patchId]['scores'][classId]

class Annotations( object ):
  def __init__( self, videoId, frameId, scaling ):
    self.videoId = videoId
    self.frameId = frameId
    self.myDict = OrderedDict()
    self.myDict[ 'annotation_filename' ] = '%s_frame_%s.json' % ( videoId, frameId )
    self.myDict[ 'frame_filename' ] = '%s_frame_%s.png' % ( videoId, frameId )
    self.myDict[ 'frame_number' ] = frameId
    self.myDict[ 'scales' ] = []
    self.scores = OrderedDict()
    self.scales = OrderedDict()
    for scale in scaling:
      self.scales[ scale ]  = []

  def addBoundingBox( self, scale, patchNum, x, y, width, height ):
    self.scales[ scale ].append( OrderedDict(
        [ ( 'patch_filename' , '%s_frame_%s_scl_%s_idx_%s.png' % ( self.videoId,
                                                                 self.frameId,
                                                                 scale,
                                                                 patchNum ) ),
           ( 'patch' , OrderedDict( [
             ( 'x' , x ),
             ( 'y' , y ),
             ( 'width' , width ),
             ( 'height' , height)
             ] )
            ) ] ) )

  def saveScore( self, patchFileName, scores ):
    scale = patchFileName.split('_')[ 4 ]
    self.scores[ ( scale, os.path.basename( patchFileName ) ) ] = scores

  def dump( self, fileName ):
    self.myDict[ "scales" ] = []
    for key, value in self.scales.iteritems():
      for patch in value:
        patch[ "scores" ] = self.scores[ ( '%s' % key, patch[ 'patch_filename'] ) ]
      self.myDict[ 'scales' ].append( {
        'scale': key,
        'patches': value
        } )
    with open( fileName, "w" ) as f:
      json.dump( self.myDict, f, indent=2 )

import caffe
class TestNet( object ):
  def __init__( self, pretrained_file, classes ):
    self.pretrained_file = pretrained_file 
    self.classes = classes
    baseScriptDir = os.path.dirname(os.path.realpath(__file__))
    self.model_file = os.path.join( baseScriptDir, "logo_val.prototxt" )
    self.test_net = None
  
  def prepareImageList( self, frameNum, patchList ):
    with open( "image_list.txt", "w" ) as f:
      for patchFileName in patchList:
        f.write( "%s 0\n" % patchFileName )
      f.write( "\n" )

  def computeScores( self, frameNum, patchList ):
    self.prepareImageList( frameNum, patchList )
    self.test_net = caffe.Net( self.model_file, self.pretrained_file )
    self.test_net.set_phase_test()
    self.test_net.set_mode_gpu()
    output = self.test_net.forward()
    probablities = output['prob']
    numOfClasses = len( self.classes )
    scores = {}
    for i in range( 0, output[ 'label' ].size ):
      scores[ i ] = {}
      for j in range( 0, numOfClasses ):
        scores[ i ][ self.classes[ j ] ] = probablities.item( numOfClasses * i + j )
    return scores

class LogoPipeline( object ):
  def run( self ):
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
    outputDir = sys.argv[ 3 ]
    outputFramesDir = os.path.join( outputDir, "frames" )
    outputPatchesDir = os.path.join( outputDir, config[ 'sliding_window' ][ 'folders' ]["patch_output" ] )
    outputJsonDir = os.path.join( outputDir, config[ 'sliding_window' ][ 'folders' ]["annotation_output"] )
    frameStep = config[ 'sliding_window' ] [ 'frame_density' ]
    scaling = config[ 'sliding_window' ][ 'scaling' ]
    pretrained_file = config[ 'pretrained_file' ]
    classes = config[ 'classes' ]

    # Setup
    videoName = os.path.basename( videoFileName )
    videoId = videoName.split('.')[0]
    createDirIfNotExists( outputFramesDir )
    createDirIfNotExists( outputPatchesDir )
    createDirIfNotExists( outputJsonDir )
    queue = Queue()

    # Init Patch Removal
    patchRemoveQueue = Queue()
    myT = RemovePatch( patchRemoveQueue )
    myT.setDaemon( True )
    myT.start()

    myT = None

    # Get the bouding boxes
    boundingBoxes = {}
    frameNum = 1
    testnet = TestNet( pretrained_file, classes )
    while not videoFrameReader.eof or frameNum <= videoFrameReader.totalFrames:
      fileName = os.path.join( outputFramesDir, "%s_frame_%s.png" % ( videoId, frameNum ) )
      frame = videoFrameReader.getFrameWithFrameNumber( int( frameNum ) )
      while not frame:
        frame = videoFrameReader.getFrameWithFrameNumber( int( frameNum ) )
      if not myT:
        myT = MultiProcessFramePostProcessor( queue, sys.argv[ 1 ], frame.width, frame.height )
        myT.setDaemon( True )
        myT.start()

      annotations = Annotations( videoId, frameNum, scaling )
      patchFileNames = []
      for scale in scaling:
        if not boundingBoxes.get( scale ):
          boundingBoxes[ scale ] = BoundingBoxes( config, frame.width, frame.height, scale ).getBoundingBoxes()
        videoFrameReader.savePngWithFrameNumber(int(frameNum), fileName)
        patchNum = 0
        for box in boundingBoxes[ scale ]:
          patchFileName = os.path.join( outputPatchesDir, "%s_frame_%s_scl_%s_idx_%s.png" % ( videoId, int( frameNum ), scale,  patchNum ) )
          videoFrameReader.patchFromFrameNumber( frameNum, patchFileName, scale, box[ 0 ], box[ 1 ], box[ 2 ], box [ 3 ] )
          annotations.addBoundingBox( scale, patchNum, box[ 0 ], box[ 1 ], box[ 2 ], box[ 3 ] )
          patchFileNames.append( patchFileName )
          patchNum += 1
      scores = testnet.computeScores( frameNum, patchFileNames )
      for patchNum, score in scores.iteritems():
        annotations.saveScore( patchFileNames[patchNum], score )
      annotations.dump( 
          os.path.join( outputJsonDir, '%s_frame_%s.json'  % ( videoId, frameNum ) ) )
      queue.put( os.path.join( outputJsonDir, '%s_frame_%s.json'  % ( videoId, frameNum ) ) )
      frameNum += frameStep
      for f in patchFileNames:
      	patchRemoveQueue.put( f )
