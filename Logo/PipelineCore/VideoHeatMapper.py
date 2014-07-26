import sys, os, glob, time
from collections import OrderedDict
from Queue import PriorityQueue
import numpy as np
import logging

import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter

class VideoHeatMapper(object):
  def __init__(self, configReader, videoFileName, videoOutputFolder, videoHeatMapperQueue):
    """Initialize values"""
    logging.debug("Initializing VideoHeatMapper")
    self.videoFileName = videoFileName
    self.videoOutputFolder = videoOutputFolder
    self.videoHeatMapperQueue = videoHeatMapperQueue
    self.startFrameNumber = configReader.ci_videoFrameNumberStart
    self.frameStep = configReader.sw_frame_density
    #self.nonBackgroundClassIds = configReader.ci_nonBackgroundClassIds
    #TODO: change
    self.nonBackgroundClassIds = configReader.ci_allClassIds
    self.videoHeatMaps = OrderedDict()
    self.numpyDictQueue = PriorityQueue()
    self.sleeptime = 30

  def run(self):
    """Create videos"""
    # Load video - since no expilicit synchronization exists to check if
    # VideoReader is ready, wait for 10 seconds
    videoFrameReader = VideoReader.VideoFrameReader(40, 40, self.videoFileName)
    videoFrameReader.generateFrames()
    time.sleep(10)

    # Get frame dimensions and create bounding boxes
    frame = videoFrameReader.getFrameWithFrameNumber(1)
    while not frame:
      frame = videoFrameReader.getFrameWithFrameNumber(1)
    imageDim = Rectangle.rectangle_from_dimensions(frame.width, frame.height)
    fps = videoFrameReader.fps

    # Create as many videos as non background classes
    videoBaseName = os.path.basename(self.videoFileName).split('.')[0]
    videoExt = os.path.basename(self.videoFileName).split('.')[-1]
    for classId in self.nonBackgroundClassIds:
      outVideoFileName = os.path.join(self.videoOutputFolder, \
        "%s_%s.%s" % (videoBaseName, str(classId), videoExt))
      logging.debug("Videos to create: %s" % outVideoFileName)
      self.videoHeatMaps[classId] = VideoWriter(outVideoFileName, fps, imageDim)

    # Initialize values
    numpyFileName = None
    jsonReaderWriter = None
    lclzPixelMaps = None
    currentFrameNum = self.startFrameNumber # frame number being extracted
    while (not videoFrameReader.eof) or (currentFrameNum <= videoFrameReader.totalFrames):
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
      while not frame:
        frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
      logging.debug("Adding frame %d to heatmap video" % currentFrameNum)
      # Check to see if this frame is supposed to have localization saved
      self.addHeatmapToNumpyDictQueue()
      if (currentFrameNum % self.frameStep) == self.startFrameNumber:
        # Loop until we have the right json file and localization
        jsonReaderWriter = None
        while jsonReaderWriter is None:
          logging.debug("Frame: %d, NpyQ size: %d, HeatQ: %d" % (\
            currentFrameNum, self.numpyDictQueue.qsize(), self.videoHeatMapperQueue.qsize()))
          try:
            numpyDict = self.numpyDictQueue.get_nowait()
            if numpyDict[0] == currentFrameNum:
              jsonFileName = numpyDict[1][0]
              numpyFileName = numpyDict[1][1]
              jsonReaderWriter = JSONReaderWriter(jsonFileName)
              lclzPixelMaps = np.load(numpyFileName)
              break
            else:
              # Put dict back in to queue
              self.numpyDictQueue.put(numpyDict)
              time.sleep(self.sleeptime)
              self.addHeatmapToNumpyDictQueue()
          except:
            time.sleep(self.sleeptime)
            self.addHeatmapToNumpyDictQueue()
      # now, write to video
      imageFileName = os.path.join(self.videoOutputFolder, "temp_%d.png" % currentFrameNum)
      videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), str(imageFileName))
      for classId in self.nonBackgroundClassIds:
        imgLclz = ImageManipulator(imageFileName)
        imgLclz.addPixelMap(lclzPixelMaps[classId])
        for lclzPatch in jsonReaderWriter.getLocalizations(classId):
          bbox = Rectangle.rectangle_from_json(lclzPatch['bbox'])
          score = float(lclzPatch['score'])
          label = str(classId) + (": %.2f" % score)
          imgLclz.addLabeledBbox(bbox, label)
        # also add frame number label - indicate if heatmap from this frame
        bbox = Rectangle.rectangle_from_endpoints(1,1,250,35)
        label = "Frame: %d" % currentFrameNum
        if (currentFrameNum % self.frameStep) == self.startFrameNumber:
          label = "Frame: %d*" % currentFrameNum
        imgLclz.addLabeledBbox(bbox, label)
        self.videoHeatMaps[classId].addFrame(imgLclz)
      # remove files from system:
      try:
        os.remove(imageFileName)
        os.remove(numpyFileName)
      except OSError:
        pass
      # increment frame number
      currentFrameNum += 1
    logging.debug("Saving heatmap videos")
    # Once video is done, save all files
    for classId in self.nonBackgroundClassIds:
      self.videoHeatMaps[classId].save()
    # HACK: quit video reader gracefully
    currentFrameNum = videoFrameReader.totalFrames
    while not videoFrameReader.eof or currentFrameNum <= videoFrameReader.totalFrames:
      videoFrameReader.seekToFrameWithFrameNumber(currentFrameNum)
      currentFrameNum += 1
    # When all work is done, only then consume the last items
    while self.videoHeatMapperQueue.qsize() > 0:
      self.videoHeatMapperQueue.get()
      self.videoHeatMapperQueue.task_done()
    logging.info("Finished creating heatmap videos")

  def addHeatmapToNumpyDictQueue(self):
    """Add to numpyDictQueue until videoHeatMapperQueue is empty"""
    while True:
      try:
        numpyDict = self.videoHeatMapperQueue.get_nowait()
        if numpyDict is "PoisonPill":
          # in case we are end of producer, put it back in queue and
          # wait for the video writer to clear it
          self.videoHeatMapperQueue.put(numpyDict)
          self.videoHeatMapperQueue.task_done()
        else:
          self.numpyDictQueue.put(numpyDict)
          self.videoHeatMapperQueue.task_done()
      except:
        break
