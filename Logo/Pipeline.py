import os, time

from multiprocessing import Queue, Process
import logging

import VideoReader
from ConfigReader import ConfigReader
from Rectangle import Rectangle
from BoundingBoxes import BoundingBoxes
from JSONReaderWriter import JSONReaderWriter

class Pipeline( object ):
  def __init__(self, configFileName, videoFileName, outputDir):
    """Initialize values"""
    self.configReader = ConfigReader(configFileName)
    self.videoFileName = videoFileName

    # sliding window creation
    self.frameStep = self.configReader.sw_frame_density
    self.scales = self.configReader.sw_scales
    self.numFramesPerLeveldb = self.configReader.ci_numFramesPerLeveldb

    # folder to save files
    self.outputFramesDir = os.path.join(outputDir, self.configReader.sw_folders_frame)
    self.outputPatchesDir = os.path.join(outputDir, self.configReader.sw_folders_patch)
    self.outputJsonDir = os.path.join(outputDir, self.configReader.sw_folders_annotation)
    self.outputLeveldbDir = os.path.join(outputDir, self.configReader.sw_folders_leveldb)
    ConfigReader.mkdir_p(self.outputFramesDir)
    ConfigReader.mkdir_p(self.outputPatchesDir)
    ConfigReader.mkdir_p(self.outputJsonDir)
    ConfigReader.mkdir_p(self.outputLeveldbDir)

    # prefix for all frames/patches:
    self.videoId = os.path.basename(videoFileName).split('.')[0]

    # logging levels
    logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
      level=self.configReader.log_level)

  def run( self ):
    videoFrameReader = VideoReader.VideoFrameReader(40, 40, self.videoFileName)
    videoFrameReader.generateFrames()
    time.sleep(1)

    # get dimensions and create bounding boxes
    frame = videoFrameReader.getFrameWithFrameNumber(1)
    while not frame:
      frame = videoFrameReader.getFrameWithFrameNumber(1)
    imageDim = Rectangle.rectangle_from_dimensions(frame.width, frame.height)
    patchDimension = Rectangle.rectangle_from_dimensions(\
      self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    staticBoundingBoxes = BoundingBoxes(imageDim, \
      self.configReader.sw_xStride, self.configReader.sw_xStride, patchDimension)

    # setup queues - since each object going into the queue needs to be
    # pickled, only include file names in the queue
    leveldbQueue = Queue()
    postProcessQueue = Queue()

    # initialize variables
    frameNum = 1
    frameCounter = 0
    leveldbId = 0
    leveldbPatchCounter = 0
    leveldbPyBlobFolder = None
    leveldbPyBlob = None
    jsonNamesInPyBlob = None
    # main loop to go through video
    while leveldbPatchCounter >= 0:
      if ((frameCounter %  self.numFramesPerLeveldb) == 0):
        # for a set of frames, create leveldb and put in queue for testnet
        if leveldbPyBlob != None:
          logging.debug("Leveldb ID: %d" % (leveldbId))
          leveldbPyBlob.save()
          leveldbQueue.put({'blob_folder': leveldbPyBlobFolder, 'jsons': jsonNamesInPyBlob})
        frameCounter = 0
        jsonNamesInPyBlob = []
        leveldbPyBlobFolder = os.path.join(self.outputLeveldbDir, "%s_leveldb_%d" % (self.videoId, leveldbId))
        # TODO: Remove comment and test
        #leveldbPyBlob = videoFrameReader.getNewPyBlob(leveldbPyBlobFolder)
        leveldbId += 1
      # extract patches, save JSON and save to leveldb
      frameName = os.path.join(self.outputFramesDir, "%s_frame_%s.png" % (self.videoId, frameNum))
      jsonName = os.path.join(self.outputJsonDir, "%s_frame_%s.json" % (self.videoId, frameNum))
      jsonNamesInPyBlob += [jsonName]
      # save annotation
      jsonAnnotation = JSONReaderWriter(jsonName, create_new=True)
      jsonAnnotation.initializeJSON(self.videoId, frameNum, self.scales)
      # put patch into leveldb
      patchNum = 0
      for scale in self.scales:
        for box in staticBoundingBoxes.getBoundingBoxes(scale):
          # Generate leveldb
          # TODO: Remove comment and test
          #leveldbPatchCounter = leveldbPyBlob.savePatch(frameNum, scale, box[0], box[1], box[2], box [3])
          # save to json
          jsonAnnotation.addPatch(scale, patchNum, leveldbPatchCounter, box[0], box[1], box[2], box [3])
          patchNum += 1
          # TODO: Remove:
          leveldbPatchCounter += 1
      jsonAnnotation.saveState()
      frameNum += self.frameStep
      frameCounter += 1
      logging.debug("Finished working on frame %d, Patch %d" % (frameNum, leveldbPatchCounter))
      # TODO: Remove:
      if frameCounter >= 10:
        leveldbPatchCounter = -1
    # for the last leveldb group, save and put in queue (but avoid double counting if only 1 leveldb)
    if (leveldbPyBlob != None) and (frameCounter > 1):
      leveldbPyBlob.save()
      leveldbQueue.put({'blob_folder': leveldbPyBlobFolder, 'jsons': jsonNamesInPyBlob})

    # join all threads

    # quite video reader gracefully
    frameNum = videoFrameReader.totalFrames
    while not videoFrameReader.eof or frameNum <= videoFrameReader.totalFrames:
      videoFrameReader.seekToFrameWithFrameNumber(frameNum)
      frameNum += 1
