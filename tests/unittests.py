#!/usr/bin/python
import unittest
import random

from Logo.PipelineCore.JSONReaderWriter import FrameInfo
from Logo.PipelineCore.JSONReaderWriter import Writer
from Logo.PipelineMath.PixelMap import PixelMap
from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

class TestFrameInfo(unittest.TestCase):

  def testBasic( self ):
    frameInfo = FrameInfo()

    # Basic Setting of FrameInfo
    frameInfo.frame_number = 3
    frameInfo.frame_width = 1024

    assert frameInfo.frame_number == 3
    assert frameInfo.frame_width == 1024

  def testScores( self ):
    frameInfo = FrameInfo()

  def testLocalization( self ):
    pass

  def testCurations( self ):
    frameInfo = FrameInfo()
    frameInfo.frame_number = 1

    frameJsonWriter = Writer( frameInfo, '/tmp/save.json' )
    frameJsonWriter.write()

  def testPickle( self ):
    frameInfo = FrameInfo()
    frameInfo.frame_number = 3
    frameInfo.scale = [ 1.34, 1.25, 3.45 ]

    frameInfo.save( '/tmp/pickle.save' )

class PixelMapTest( unittest.TestCase ):

  def testNeighborMap( self ):
    return
    ''' Test NeighborMap created '''
    imageDim = Rectangle.rectangle_from_dimensions( 1280, 720 )
    patchDim = Rectangle.rectangle_from_dimensions( 256, 256 )
    xStepSize = {
      0.4 : 32,
      1: 32,
      1.4 : 32,
    }
    yStepSize = {
      0.4 : 32,
      1: 32,
      1.4 : 32,
    }
    staticBoundingBoxes = BoundingBoxes(imageDim, xStepSize, yStepSize, patchDim)
    allCellBoundariesDict = PixelMap.getCellBoundaries(staticBoundingBoxes, [ 0.4, 1, 1.4 ])

    pass

  def testCellMap( self ):
    ''' Test the cellMap created '''
    pass


if __name__ == '__main__':
    unittest.main()
