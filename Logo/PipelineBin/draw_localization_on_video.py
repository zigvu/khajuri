#!/usr/bin/python

import sys, os, glob, time
from collections import OrderedDict
from Queue import PriorityQueue
import numpy as np
import logging

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle

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
  # Logging levels
  logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
    level=configReader.log_level)

  # Set up
  logging.info("Setting up video %s" % videoFileName)

  videoBaseName = os.path.basename(videoFileName).split('.')[0]
  videoExt = os.path.basename(videoFileName).split('.')[-1]
  outVideoFileName = os.path.join(outputFolder, "%s_localization.%s" % (videoBaseName, videoExt))
  ConfigReader.mkdir_p(outputFolder)

  # Read all JSONs
  frameIndex = {}
  jsonFiles = glob.glob(os.path.join(jsonFolder, "*json"))
  for jsonFileName in jsonFiles:
    logging.debug("Reading json %s" % os.path.basename(jsonFileName))
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    frameNumber = jsonReaderWriter.getFrameNumber()
    frameIndex[frameNumber] = jsonFileName
  logging.info("Total of %d json indexed" % len(frameIndex.keys()))

  # Load video - since no expilicit synchronization exists to check if
  # VideoReader is ready, wait for 10 seconds
  videoFrameReader = VideoReader.VideoFrameReader(40, 40, videoFileName)
  videoFrameReader.generateFrames()
  time.sleep(10)

  # Get frame dimensions and create bounding boxes
  frame = videoFrameReader.getFrameWithFrameNumber(1)
  while not frame:
    frame = videoFrameReader.getFrameWithFrameNumber(1)
  imageDim = Rectangle.rectangle_from_dimensions(frame.width, frame.height)
  fps = videoFrameReader.fps

  videoWriter = VideoWriter(outVideoFileName, fps, imageDim)
  currentFrameNum = configReader.ci_videoFrameNumberStart # frame number being extracted
  jsonReaderWriter = None
  while (not videoFrameReader.eof) or (currentFrameNum <= videoFrameReader.totalFrames):
    frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
    while not frame:
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
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

  # HACK: quit video reader gracefully
  currentFrameNum = videoFrameReader.totalFrames
  while not videoFrameReader.eof or currentFrameNum <= videoFrameReader.totalFrames:
    videoFrameReader.seekToFrameWithFrameNumber(currentFrameNum)
    currentFrameNum += 1

  # Save and exit
  videoWriter.save()
  logging.info("Finished creating video")
