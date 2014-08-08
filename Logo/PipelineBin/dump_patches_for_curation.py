#!/usr/bin/env python
import sys, os, time
import logging

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.CurationManager import CurationManager

if __name__ == "__main__":
  if len( sys.argv ) < 5:
    print 'Usage %s <config.yaml> <videoFileName> <jsonFolder> <outputFolder>' % sys.argv[ 0 ]
    sys.exit( 1 )
  configFileName = sys.argv[ 1 ]
  videoFileName = sys.argv[ 2 ]
  jsonFolder = sys.argv[ 3 ]
  outputFolder = sys.argv[ 4 ]

  configReader = ConfigReader(configFileName)
  # Logging levels
  logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
    level=configReader.log_level)

  # Set up
  logging.info("Setting up patch extraction for %s" % videoFileName)
  ConfigReader.mkdir_p(outputFolder)

  videoFrameReader = VideoReader.VideoFrameReader( 40, 40, videoFileName )
  videoFrameReader.generateFrames()
  time.sleep( 10 )
  curationManager = CurationManager(jsonFolder, configReader)
  for frameNumber in curationManager.getFrameNumbers():
    logging.debug("Working on frame number %d" % frameNumber)
    
    # Save the frame File first
    frameFileName = os.path.join(outputFolder, "frame_%s.png" % frameNumber )
    frame = videoFrameReader.getFrameWithFrameNumber( frameNumber )
    while not frame:
      frame = videoFrameReader.getFrameWithFrameNumber( frameNumber )
    videoFrameReader.savePngWithFrameNumber(int(frameNumber), frameFileName)

    # Get the patches from the frame file
    for curationPatch in curationManager.getCurationPatches(frameNumber):
      bbox = Rectangle.rectangle_from_json(curationPatch['bbox'])
      patchFolderName = os.path.join(outputFolder, curationPatch['patch_foldername'])
      ConfigReader.mkdir_p(patchFolderName)
      patchFileName = os.path.join(patchFolderName, curationPatch['patch_filename'])
      imageManipulator = ImageManipulator(frameFileName)
      imageManipulator.extract_patch(bbox, patchFileName, \
        configReader.sw_patchWidth, configReader.sw_patchHeight)

    # Remove the frame which is not needed
    os.remove( frameFileName )

  # HACK: quit video reader gracefully
  frameNumber = videoFrameReader.totalFrames
  while not videoFrameReader.eof or frameNumber <= videoFrameReader.totalFrames:
    videoFrameReader.seekToFrameWithFrameNumber(frameNumber)
    frameNumber += 1

  # Exit
  logging.info("Finished creating patches")
