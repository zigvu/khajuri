#!/usr/bin/python

import sys, os, glob
from collections import OrderedDict
import logging

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineMath.Rectangle import Rectangle

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter
from Logo.PipelineCore.ConfigReader import ConfigReader

if __name__ == '__main__':
  if len(sys.argv) < 4:
    print 'Usage %s <config.yaml> <videoFileName> <jsonFolder> <outputFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  jsonFolder = sys.argv[3]
  outputFolder = sys.argv[4]

  configReader = ConfigReader(configFileName)
  ConfigReader.mkdir_p(outputFolder)
  # Logging levels
  logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
    level=configReader.log_level)

  # Set up
  logging.info("Setting up video %s" % videoFileName)

  videoFrameReader = VideoFrameReader(videoFileName)
  fps = videoFrameReader.getFPS()
  imageDim = videoFrameReader.getImageDim()

  # Read all JSONs
  frameIndex = {}
  jsonFiles = glob.glob(os.path.join(jsonFolder, "*json"))
  for jsonFileName in jsonFiles:
    logging.debug("Reading json %s" % os.path.basename(jsonFileName))
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    frameNumber = jsonReaderWriter.getFrameNumber()
    frameIndex[frameNumber] = jsonFileName
  logging.info("Total of %d json indexed" % len(frameIndex.keys()))

  # Set up output video
  videoBaseName = os.path.basename(videoFileName).split('.')[0]
  outVideoFileName = os.path.join(outputFolder, "%s_localization.avi" % (videoBaseName))
  videoWriter = VideoWriter(outVideoFileName, fps, imageDim)

  # Go through video frame by frame
  currentFrameNum = configReader.ci_videoFrameNumberStart # frame number being extracted
  jsonReaderWriter = None
  frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
  while frame != None:
    logging.debug("Adding frame %d to video" % currentFrameNum)
    if currentFrameNum in frameIndex.keys():
      jsonReaderWriter = JSONReaderWriter(frameIndex[currentFrameNum])

    # Save each frame
    imageFileName = os.path.join(outputFolder, "temp_%d.png" % currentFrameNum)
    videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), str(imageFileName))
    imgLclz = ImageManipulator(imageFileName)

    # Add bounding boxes
    for classId in configReader.ci_nonBackgroundClassIds:
      for lclzPatch in jsonReaderWriter.getLocalizations(classId):
        bbox = Rectangle.rectangle_from_json(lclzPatch['bbox'])
        score = float(lclzPatch['score'])
        label = str(classId) + (": %.2f" % score)
        imgLclz.addLabeledBbox(bbox, label)
    # also add frame number label - indicate if scores from this frame
    bbox = Rectangle.rectangle_from_endpoints(1,1,250,35)
    label = "Frame: %d" % currentFrameNum
    if currentFrameNum in frameIndex.keys():
      label = "Frame: %d*" % currentFrameNum
    imgLclz.addLabeledBbox(bbox, label)
    # Add to video and remove temp file
    videoWriter.addFrame(imgLclz)
    os.remove(imageFileName)
    # increment frame number
    currentFrameNum += 1
    frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))

  # Close video reader
  videoFrameReader.close()

  # Save and exit
  videoWriter.save()
  logging.info("Finished creating video")
