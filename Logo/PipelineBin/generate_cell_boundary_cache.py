#!/usr/bin/env python 

import sys, os, glob, logging
from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineMath.PixelMap import PixelMap
from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

if __name__ == '__main__':
  if len(sys.argv) < 4:
    print 'Usage %s <config.yaml> <frame.width> <frame.height>' % sys.argv[ 0 ]
    sys.exit(1)
  logging.basicConfig(
    format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
    level=logging.INFO, datefmt="%Y-%m-%d--%H:%M:%S")

  configFileName = sys.argv[1]
  frameWidth = sys.argv[2]
  frameHeight = sys.argv[3]
  configReader = ConfigReader(configFileName)
  imageDim = Rectangle.rectangle_from_dimensions( int( frameWidth ), int( frameHeight ) )
  patchDimension = Rectangle.rectangle_from_dimensions(\
      configReader.sw_patchWidth, configReader.sw_patchHeight)
  staticBoundingBoxes = BoundingBoxes(imageDim, \
      configReader.sw_xStride, configReader.sw_yStride, patchDimension)
  logging.info( 'Starting to get cell boundaries' )
  allCellBoundariesDict = PixelMap.getCellBoundaries(staticBoundingBoxes, 
      configReader.sw_scales)
  logging.info( 'Done with calculating cell boundaries.' )


