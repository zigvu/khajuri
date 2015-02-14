#!/usr/bin/python

import glob, sys
import os, errno

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineCore.TestPostProcessors import TestPostProcessors
from Logo.PipelineCore.ConfigReader import ConfigReader

if __name__ == '__main__':
  if len(sys.argv) < 6:
    print 'Usage %s <config.yaml> <testMode> <imageFolder> <outputFolder>' % sys.argv[ 0 ]
    print 'Test modes (integer):'
    print '\t1: Test PixelMapper\n\t2: Test ScaleSpaceCombiner\n\t3: Test FramePostProcessor'
    print '\t4: Test CurationManager\n\t5: Test VideoWriter\n'
    sys.exit(1)

  configFileName = sys.argv[1]
  testMode = int(sys.argv[2])
  imageFolder = sys.argv[3]
  outputFolder = sys.argv[4]
  # TODO: replace from video frame information
  imageDim = Rectangle.rectangle_from_dimensions(1280, 720)
  testPostProcessors = TestPostProcessors(configFileName, imageDim)
  configReader = ConfigReader(configFileName)
  jsonFolder = configReader.sw_folders_json
  jsonFiles = glob.glob(os.path.join(jsonFolder, "*json")) + \
    glob.glob(os.path.join(jsonFolder, "*snappy"))
  
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
  elif (testMode == 5):
    testPostProcessors.test_videoWriter(jsonFolder, imageFolder, outputFolder)

