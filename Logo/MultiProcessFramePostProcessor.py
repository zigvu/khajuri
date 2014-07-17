import Queue, sys, os
import multiprocessing
from multiprocessing import Process
import threading, time, pdb, glob

from Rectangle import Rectangle
from BoundingBoxes import BoundingBoxes
from ConfigReader import ConfigReader
from JSONReaderWriter import JSONReaderWriter
from PixelMapper import PixelMapper
from ImageManipulator import ImageManipulator
from ScaleSpaceCombiner import ScaleSpaceCombiner
from FramePostProcessor import FramePostProcessor
from CurationManager import CurationManager
from VideoWriter import VideoWriter
import logging, os

def startFramePostProcessor( jsonFileName, configReader, staticBoundingBoxes ):
  jsonReaderWriter = JSONReaderWriter( jsonFileName )
  framePostProcessor = FramePostProcessor(
      jsonReaderWriter, 
      staticBoundingBoxes, 
      configReader)
  framePostProcessor.run()

class MultiProcessFramePostProcessor( threading.Thread ):
  def __init__( self, queue, configFileName, width, height ):
    super(MultiProcessFramePostProcessor, self).__init__()
    self.queue = queue
    self.processLimit = multiprocessing.cpu_count()
    self.configReader = ConfigReader(configFileName)
    imageDim = Rectangle.rectangle_from_dimensions( 
        width,  
        height )
    patchDimension = Rectangle.rectangle_from_dimensions(\
      self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    self.staticBoundingBoxes = BoundingBoxes(imageDim, \
      self.configReader.sw_xStride, self.configReader.sw_xStride, patchDimension)

  def run( self ):
    while True:
      children = multiprocessing.active_children()
      if len( children ) < self.processLimit:
        self.startNewJob()
      time.sleep( 1 )

  def startNewJob( self ):
    try:
      jsonFile = self.queue.get( False )
      p = multiprocessing.Process( target=startFramePostProcessor, kwargs={ 
        'jsonFileName' : jsonFile,
        'configReader' : self.configReader,
        'staticBoundingBoxes' : self.staticBoundingBoxes,
        } )
      p.start()
    except Queue.Empty:
     pass

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../VideoReader'% baseScriptDir  )
import VideoReader

if __name__ == "__main__":
  if len( sys.argv ) < 4:
    print 'Usage %s <config.yaml> <video.file> <json.dir>' % sys.argv[ 0 ]
    sys.exit( 1 )
  videoFileName = sys.argv[ 2 ]
  videoFrameReader = VideoReader.VideoFrameReader( 40, 40, videoFileName )
  videoFrameReader.generateFrames()
  import time
  time.sleep( 1 )
  frame = videoFrameReader.getFrameWithFrameNumber( 1 )
  while not frame:
    frame = videoFrameReader.getFrameWithFrameNumber( 1 )
  queue = Queue.Queue()
  myT = MultiProcessFramePostProcessor( queue, sys.argv[ 1 ], frame.width, frame.height )
  myT.setDaemon( True )
  myT.start()
  for f in glob.glob( "%s/*json" % sys.argv[ 3 ]):
    queue.put( f )
  while len( multiprocessing.active_children() ) > 0 or queue.qsize() > 0:
    time.sleep( 10 )
  print 'Done - ignore the core dump'
