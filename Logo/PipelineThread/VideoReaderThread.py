import os, time
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager
from threading import Thread
from collections import OrderedDict
import json
import logging
import threading

import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.CaffeNet import CaffeNet

from Logo.PipelineThread.PostProcessThread import PostProcessThread
from Logo.PipelineThread.PostProcessThread import framePostProcessorRun

class VideoReaderThread( Thread ):
  """ Class for extracting frames from video """
  def __init__( self, leveldbQueue, leveldbFolder, jsonFolder, videoFileName, configReader, frameStartNum ):
    super(VideoReaderThread, self).__init__()
    self.leveldbQueue = leveldbQueue
    self.leveldbFolder = leveldbFolder
    self.jsonFolder = jsonFolder
    self.videoFileName = videoFileName
    self.configReader = configReader
    self.scales = self.configReader.sw_scales
    self.frameStep = self.configReader.sw_frame_density
    self.videoFrameReader = VideoReader.VideoFrameReader(40, 40, self.videoFileName)
    self.videoFrameReader.generateFrames()
    self.videoFrameReader.startLogger()

    # Load video - since no expilicit synchronization exists to check if
    # VideoReader is ready, wait for 10 seconds
    time.sleep(10)

    # Get frame dimensions and create bounding boxes
    self.frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    while not self.frame:
      self.frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    self.imageDim = Rectangle.rectangle_from_dimensions(self.frame.width, self.frame.height)
    self.patchDimension = Rectangle.rectangle_from_dimensions(\
      self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    self.staticBoundingBoxes = BoundingBoxes(self.imageDim, \
      self.configReader.sw_xStride, self.configReader.sw_yStride, self.patchDimension)

    self.fps = self.videoFrameReader.fps
    self.lengthInMicroSeconds = self.videoFrameReader.lengthInMicroSeconds
    self.totalNumOfFrames = int(self.fps * self.lengthInMicroSeconds / 1000000.0)

    #self.startFrameNumber = self.configReader.ci_videoFrameNumberStart
    self.startFrameNumber = frameStartNum
    self.numFramesPerLeveldb = self.configReader.ci_numFramesPerLeveldb
    self.leveldbFolderSize = self.configReader.ci_maxLeveldbSizeMB

    # Video name prefix for all frames/patches:
    self.videoId = os.path.basename(videoFileName).split('.')[0]
    self.gpu_devices = self.configReader.ci_gpu_devices
 
  def run( self ):
    """ Spawn as many processes as there are GPUs"""
    logging.info( 'Starting VideoFrameReader...' )
    videoFrameReaderProcess = []
    numOfGpus = len( self.gpu_devices )
    for i in range( numOfGpus ):
      p = Process( target=startVideoReaderProcess, 
          args=(self, self.startFrameNumber + ( i * self.frameStep ),
            self.frameStep * numOfGpus) )
      p.start()
      logging.info( 'Starting VideoFrameReader Process %s' % p)
      videoFrameReaderProcess.append( p )

    for p in videoFrameReaderProcess:
      logging.info( 'Waiting for all VideoFrameReader Processes to complete...')
      p.join()
    logging.info( 'Done with all processors for VideoFrameReader.' )

def startVideoReaderProcess( self, frameStart, frameStep ):
  """ Run the VideoReader Thread """
  # Initialize variables
  currentFrameNum = frameStart # frame number being extracted
  extractedFrameCounter = 0               # total number of extracted frames
  curLeveldbFolder = None                 # folder where to write leveldb
  videoDb = None                          # db object from VideoReader
  leveldbMapping = None                   # mapping between patches in leveldb and corresponding jsons
  leveldbId = 0                           # number of leveldb created

  videoFrameReader = VideoReader.VideoFrameReader(40, 40, self.videoFileName)
  videoFrameReader.generateFrames()

  # Load video - since no expilicit synchronization exists to check if
  # VideoReader is ready, wait for 10 seconds
  time.sleep(10)
  
  # Main loop to go through video
  logging.info("Start patch extraction")
  while (not videoFrameReader.eof) or (currentFrameNum <= videoFrameReader.totalFrames):
    # Create new leveldbs for each set of numFramesPerLeveldb frames
    if ((extractedFrameCounter %  self.numFramesPerLeveldb) == 0):
      # If ready, save leveldb and put in queue for CaffeNet
      if videoDb != None:
        logging.info("Saving db ID: %d, extractedFrameCounter: %s, self.numFramesPerLeveldb: %s" % (leveldbId, extractedFrameCounter, self.numFramesPerLeveldb))
        videoDb.saveDb()
        with open(leveldbMappingFile, "w") as f :
          json.dump(leveldbMapping, f, indent=2)
        self.leveldbQueue.put(curLeveldbFolder)
      # If leveldb folder is full, wait until dump
      if self.leveldbFolderSize > 0:
        leveldbFolderSize = ConfigReader.dir_size(self.leveldbFolder)
        while leveldbFolderSize >= self.leveldbFolderSize:
          logging.info("Waiting for leveldb folder to empty")
          time.sleep(5)
          leveldbFolderSize = ConfigReader.dir_size(self.leveldbFolder)
      # Set up new levedb
      extractedFrameCounter = 0
      leveldbPatchCounter = 0
      curLeveldbFolder = os.path.join(self.leveldbFolder, "%s_leveldb_%s_%d" % (self.videoId, os.getpid(), leveldbId))
      leveldbMappingFile = os.path.join(curLeveldbFolder, "leveldb_mapping.json")
      videoDb = VideoReader.VideoDb(VideoReader.VideoDb.DBTYPE.LEVELDB, 1000)
      videoDb.createNewDb(curLeveldbFolder, videoFrameReader)
      leveldbMapping = OrderedDict()
      leveldbId += 1
      logging.info("%d percent video processed" % (int(100.0 * currentFrameNum/self.totalNumOfFrames)))
    # Start json annotation file
    jsonName = os.path.join(self.jsonFolder, "%s_frame_%s.json" % (self.videoId, currentFrameNum))
    jsonAnnotation = JSONReaderWriter(jsonName, create_new=True)
    jsonAnnotation.initializeJSON(self.videoId, currentFrameNum, self.imageDim, self.scales)
    # Put patch into leveldb
    for scale in self.scales:
      patchNum = 0
      for box in self.staticBoundingBoxes.getBoundingBoxes(scale):
        # Generate leveldb patch and add to json
        leveldbPatchCounter = videoDb.savePatch(currentFrameNum, scale, \
          box[0], box[1], box[2], box [3])
        jsonAnnotation.addPatch(scale, patchNum, leveldbPatchCounter, \
          box[0], box[1], box[2], box [3])
        leveldbMapping[leveldbPatchCounter] = jsonName
        # Increment counters
        patchNum += 1
    # Save annotation file
    jsonAnnotation.saveState()
    currentFrameNum += frameStep
    extractedFrameCounter += 1
  # end while

  # For the last leveldb group, save and put in queue
  if videoDb != None:
    logging.info("Saving leveldb ID: %d" % (leveldbId))
    videoDb.saveDb()
    with open(leveldbMappingFile, "w") as f :
      json.dump(leveldbMapping, f, indent=2)
    self.leveldbQueue.put(curLeveldbFolder)

  # HACK: work around so that videoDb releases lock on curLeveldbFolder
  videoDb = None
  # HACK: quit video reader gracefully
  currentFrameNum = videoFrameReader.totalFrames
  while not videoFrameReader.eof or currentFrameNum <= videoFrameReader.totalFrames:
    videoFrameReader.seekToFrameWithFrameNumber(currentFrameNum)
    currentFrameNum += 1

  # Put poison pills and wait to join all threads
  logging.info("Done with all patch extraction. Waiting for caffe thread to join")
  self.leveldbQueue.put(None)
