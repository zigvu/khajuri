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
  if len( sys.argv ) < 6:
    print 'Usage %s <config.yaml> <videoFileName> <jsonFolder> <outputFolder> <classId>' % sys.argv[ 0 ]
    sys.exit( 1 )
  configFileName = sys.argv[ 1 ]
  videoFileName = sys.argv[ 2 ]
  jsonFolder = sys.argv[ 3 ]
  outputFolder = sys.argv[ 4 ]
  classId = str(sys.argv[ 5 ])

  configReader = ConfigReader(configFileName)
  # Logging levels
  logging.basicConfig(format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s', 
    level=configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

  # Set up
  logging.info("Setting up frame extraction for %s" % videoFileName)
  ConfigReader.mkdir_p(outputFolder)

  videoFrameReader = VideoReader.VideoFrameReader( 40, 40, videoFileName )
  videoFrameReader.generateFrames()
  time.sleep( 10 )
  curationManager = CurationManager(jsonFolder, configReader)
  curationFrames = curationManager.getCurationFrames(classId)

  for frameNumber in curationManager.getFrameNumbers():
    if frameNumber in curationFrames.keys():
      curation = curationFrames[frameNumber]
      logging.debug("Working on frame number %d" % frameNumber)
    
      frameFolderName = os.path.join(outputFolder, curation['frame_foldername'])
      frameFileName = os.path.join(frameFolderName, curation['frame_filename'])

      frame = videoFrameReader.getFrameWithFrameNumber( frameNumber )
      while not frame:
        frame = videoFrameReader.getFrameWithFrameNumber( frameNumber )
      # create folder if doesn't exist and save png
      ConfigReader.mkdir_p(frameFolderName)
      videoFrameReader.savePngWithFrameNumber(int(frameNumber), frameFileName)

  # HACK: quit video reader gracefully
  frameNumber = videoFrameReader.totalFrames
  while not videoFrameReader.eof or frameNumber <= videoFrameReader.totalFrames:
    videoFrameReader.seekToFrameWithFrameNumber(frameNumber)
    frameNumber += 1

  # Exit
  logging.info("Finished creating frames")
