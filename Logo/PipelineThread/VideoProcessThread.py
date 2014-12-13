import os, time, sys
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager
from collections import OrderedDict
import json, pickle
import logging

import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.PixelMap import PixelMap

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.VideoDbManager import VideoDbManager
from Logo.PipelineCore.VideoCaffeManager import VideoCaffeManager

from Logo.PipelineCore.CaffeNet import CaffeNet

from Logo.PipelineThread.PostProcessThread import PostProcessThread
from Logo.PipelineThread.VideoReaderThread import VideoReaderThread
from Logo.PipelineThread.PostProcessThread import framePostProcessorRun

def runVideoDbManager(sharedDict, producedQueue, consumedQueue, \
  deviceId, frmStrt, frmStp, dbFolder, newPrototxtFile):
  """Run single videoDBManager process"""
  logging.info("VideoDBManager process for deviceId %d started" % deviceId)
  configFileName = sharedDict['configFileName']
  videoFileName = sharedDict['videoFileName']
  jsonFolder = sharedDict['jsonFolder']

  videoDbManager = VideoDbManager(configFileName)
  videoDbManager.setupFolders(dbFolder, jsonFolder)
  videoDbManager.setupVideoFrameReader(videoFileName)
  videoDbManager.setupPrototxt(newPrototxtFile, deviceId)
  videoDbManager.setupQueues(producedQueue, consumedQueue)
  # finally start producing
  videoDbManager.startVideoDb(frmStrt, frmStp)

def runVideoCaffeManager(sharedDict, producedQueue, consumedQueue, \
  deviceId, newPrototxtFile):
  """Run single videoCaffeManager process"""
  configFileName = sharedDict['configFileName']
  maxProducedQueueSize = sharedDict['maxProducedQueueSize']
  
  logging.info("Waiting for videoDb queue to grow before starting VideoCaffeManager for deviceId %d" % deviceId)
  while producedQueue.qsize() < maxProducedQueueSize:
    time.sleep(5)

  logging.info("VideoCaffeManager process for deviceId %d started" % deviceId)
  videoCaffeManager = VideoCaffeManager(configFileName)
  videoCaffeManager.setupNet(newPrototxtFile, deviceId)
  videoCaffeManager.setupQueues(producedQueue, consumedQueue)
  # finally start consuming
  videoCaffeManager.startForwards()


class VideoProcessThread( object ):
  """Class responsible for starting and running caffe on video"""
  def __init__(self, configFileName, videoFileName, baseDbFolder, jsonFolder, numpyFolder):
    """Initialize values"""
    self.configFileName = configFileName
    self.videoFileName = videoFileName

    self.configReader = ConfigReader(configFileName)
    self.runPostProcessor = self.configReader.ci_runCaffePostProcessInParallel
    self.frameStep = self.configReader.sw_frame_density
    self.frameStartNumber = self.configReader.ci_videoFrameNumberStart

    # Folder to save files
    self.baseDbFolder = baseDbFolder
    self.jsonFolder = jsonFolder
    self.numpyFolder = numpyFolder
    ConfigReader.rm_rf(self.baseDbFolder)
    ConfigReader.mkdir_p(self.baseDbFolder)
    ConfigReader.mkdir_p(self.jsonFolder)
    ConfigReader.mkdir_p(self.numpyFolder)
    # Logging levels
    logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s PID:%(process)d - %(message)s', 
      level=self.configReader.log_level)

    # More than 1 GPU Available?
    self.gpu_devices = self.configReader.ci_gpu_devices

    # TODO: Move to config:
    self.maxProducedQueueSize = 6
    self.maxConsumedQueueSize = 2

  def run( self ):
    """Run the video through caffe"""
    startTime = time.time()
    logging.info("Setting up caffe run for video %s" % self.videoFileName)
    if self.runPostProcessor:
      logging.info("Setting up post-processing to run in parallel")

    # Share state with other processes - since objects need to be pickled
    # only put primitives where possible
    sharedManager = Manager()
    sharedDict = sharedManager.dict()
    sharedDict['configFileName'] = self.configFileName
    sharedDict['videoFileName'] = self.videoFileName
    sharedDict['jsonFolder'] = self.jsonFolder
    sharedDict['numpyFolder'] = self.numpyFolder
    sharedDict['maxProducedQueueSize'] = self.maxProducedQueueSize

    producedQueues = OrderedDict()
    consumedQueues = OrderedDict()
    videoDbManagerProcesses = []
    videoCaffeManagerProcesses = []

    # process in each GPU
    deviceCount = 0
    for deviceId in self.gpu_devices:
      # producer/consumer queues
      producedQueues[deviceId] = JoinableQueue(self.maxProducedQueueSize)
      consumedQueues[deviceId] = JoinableQueue(self.maxConsumedQueueSize)
      
      # start and step for frames differ by GPU
      frmStrt = self.frameStartNumber + (deviceCount * self.frameStep)
      frmStp = self.frameStep * len(self.gpu_devices)
      # folders and prototxt by GPU
      dbFolder = os.path.join(self.baseDbFolder, "id_%d" % deviceId)
      newPrototxtFile = os.path.join(self.baseDbFolder, 'prototxt_%s.prototxt' % os.path.basename(dbFolder))
      # patch producer - save to DB
      videoDbManagerProcess = Process(\
        target=runVideoDbManager,\
        args=(sharedDict, producedQueues[deviceId], consumedQueues[deviceId], \
          deviceId, frmStrt, frmStp, dbFolder, newPrototxtFile))
      videoDbManagerProcesses += [videoDbManagerProcess]
      videoDbManagerProcess.start()
      
      # patch consumer - run caffe
      videoCaffeManagerProcess = Process(\
        target=runVideoCaffeManager,\
        args=(sharedDict, producedQueues[deviceId], consumedQueues[deviceId], \
          deviceId, newPrototxtFile))
      videoCaffeManagerProcesses += [videoCaffeManagerProcess]
      videoCaffeManagerProcess.start()
      deviceCount += 1


    logging.debug("Waiting for videoDbManagerProcess process to complete.")
    for videoDbManagerProcess in videoDbManagerProcesses:
      videoDbManagerProcess.join()
    logging.debug("videoDbManagerProcess process joined")

    logging.debug("Waiting for videoCaffeManagerProcess process to complete.")
    for videoCaffeManagerProcess in videoCaffeManagerProcesses:
      videoCaffeManagerProcess.join()
    logging.debug("videoCaffeManagerProcess process joined")

    logging.debug("Waiting for queues to get joined")
    for deviceId in self.gpu_devices:
      logging.debug("producedQueues size %d" % producedQueues[deviceId].qsize())
      producedQueues[deviceId].join()
      logging.debug("consumedQueues size %d" % consumedQueues[deviceId].qsize())
      consumedQueues[deviceId].join()
    logging.debug("All queues joined")

    endTime = time.time()
    logging.info( 'It took VideoProcessThread %s seconds to complete' % ( endTime - startTime ) )
