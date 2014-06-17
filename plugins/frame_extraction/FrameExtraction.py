from random import random
import os
from plugins.Plugin import Plugin


class FrameExtraction(Plugin):
  """Frame Extraction Plugin."""
  def __init__(self, config):
    self.name = "FrameExtraction"
    self.config = config
    self.videoFrameReader = self.config["videoFrameReader"]
    self.baseFrameFolder = self.config["baseFrameFolder"]

  def process(self, frame):
    frame.vFrame = self.videoFrameReader.getFrameWithFrameNumber( int( frame.frameNumber ) )
    while not frame.vFrame:
            frame.vFrame = self.videoFrameReader.getFrameWithFrameNumber( int( frame.frameNumber ) )
    frameDir = os.path.join( self.baseFrameFolder, str( frame.frameNumber ) )
    if not os.path.exists( frameDir ):
      os.makedirs( frameDir )
    frame.imgName = os.path.join( frameDir, "original.ppm" )
    self.videoFrameReader.saveFrameWithFrameNumber( int( frame.frameNumber ), frame.imgName )

    # Create Patches            
    boundingBoxes = BoundingBoxes( frame.vFrame.width, frame.vFrame.height )
    patchNum = 1
    for box in boundingBoxes.getBoundingBoxes():
      patchFileName = os.path.join( frameDir, "patch_%s_%s.png" % ( int( frame.frameNumber ), patchNum ) )
      self.videoFrameReader.annotateFrameNumber( frame.frameNumber, patchFileName, 
          box[ 0 ], box[ 1 ], box[ 2 ], box [ 3 ] )
      patchNum += 1
    return 1, True
