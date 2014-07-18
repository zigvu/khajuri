#!/usr/bin/env python
import sys, os, time, pdb, glob, logging

from Rectangle import Rectangle
from ConfigReader import ConfigReader
from ImageManipulator import ImageManipulator
from CurationManager import CurationManager
from LogoPipeline import createDirIfNotExists

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../VideoReader'% baseScriptDir  )
import VideoReader

if __name__ == "__main__":
  if len( sys.argv ) < 5:
    print 'Usage %s <config.yaml> <video.file> <json.dir> <output.dir>' % sys.argv[ 0 ]
    sys.exit( 1 )
  configFileName = sys.argv[ 1 ]
  videoFileName = sys.argv[ 2 ]
  jsonFolder = sys.argv[ 3 ]
  outputFolder = sys.argv[ 4 ]

  createDirIfNotExists( outputFolder )

  videoFrameReader = VideoReader.VideoFrameReader( 40, 40, videoFileName )
  videoFrameReader.generateFrames()
  time.sleep( 1 )
  configReader = ConfigReader(configFileName)
  curationManager = CurationManager(jsonFolder, configReader)
  for frameNumber in curationManager.getFrameNumbers():
    
    # Save the frame File first
    frameFileName = os.path.join(outputFolder, "frame_%s.png" % frameNumber )
    frame = videoFrameReader.getFrameWithFrameNumber( frameNumber )
    while not frame:
      frame = videoFrameReader.getFrameWithFrameNumber( frameNumber )
    videoFrameReader.savePngWithFrameNumber(int(frameNumber), frameFileName)

    # Get the patches from the frame file
    for curationPatch in curationManager.getCurationPatches(frameNumber):
      bbox = Rectangle.rectangle_from_json(curationPatch['bbox'])
      patchFileName = os.path.join(outputFolder, curationPatch['patch_filename'])
      imageManipulator = ImageManipulator(frameFileName)
      imageManipulator.extract_patch(bbox, patchFileName, \
        configReader.sw_patchWidth, configReader.sw_patchHeight)

    # Remove the frame which is not needed
    os.remove( frameFileName )

  print 'Done - ignore the core dump'
