#!/usr/bin/python

import glob, sys
import os, errno

from Rectangle import Rectangle
from TestPostProcessors import TestPostProcessors

if __name__ == '__main__':
  if len(sys.argv) < 6:
    print 'Usage %s <config.yaml> <testMode> <jsonFolder> <imageFolder> <outputFolder>' % sys.argv[ 0 ]
    print 'Test modes (integer):'
    print '\t1: Test PixelMapper\n\t2: Test ScaleSpaceCombiner\n\t3: Test FramePostProcessor'
    print '\t4: Test CurationManager\n'
    sys.exit(1)

  configFileName = sys.argv[1]
  testMode = int(sys.argv[2])
  jsonFolder = sys.argv[3]
  imageFolder = sys.argv[4]
  outputFolder = sys.argv[5]
  # TODO: replace from video frame information
  imageDim = Rectangle.rectangle_from_dimensions(1280, 720)
  testPostProcessors = TestPostProcessors(configFileName, imageDim)
  jsonFiles = glob.glob(os.path.join(jsonFolder, "*json"))
  if (testMode == 1) or (testMode == 2) or (testMode == 3):
    for jsonFileName in jsonFiles:
      print "Working on " + os.path.basename(jsonFileName)
      if testMode == 1:
        testPostProcessors.test_pixelMapper(jsonFileName, imageFolder, outputFolder)
      elif testMode == 2:
        testPostProcessors.test_scaleSpaceCombiner(jsonFileName, imageFolder, outputFolder)
      elif testMode == 3:
        testPostProcessors.test_framePostProcessor(jsonFileName, imageFolder, outputFolder)
  elif (testMode == 4):
    testPostProcessors.test_curationManager(jsonFolder, imageFolder, outputFolder)

