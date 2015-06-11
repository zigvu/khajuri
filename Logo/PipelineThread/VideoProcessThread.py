import os, time, sys, glob
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager
from threading import Thread
from collections import OrderedDict
import json, pickle
import logging
import Queue

import VideoReader

from config.Config import Config
from Logo.PipelineCore.VideoFrameReader import VideoFrameReader

from Logo.PipelineCore.VideoDbManager import VideoDbManager
from Logo.PipelineCore.VideoCaffeManager import VideoCaffeManager
from Logo.PipelineCore.Version import LogoVersion

from postprocessing.task.CaffeResultPostProcess import CaffeResultPostProcess
from infra.Pipeline import Pipeline


config = None

def runVideoDbManager(sharedDict, producedQueue, consumedQueue, \
  deviceId, frmStrt, frmStp, dbFolder, newPrototxtFile):
  """Run single videoDBManager process"""
  logging.info("VideoDBManager process for deviceId %d started" % deviceId)
  videoFileName = sharedDict['videoFileName']
  jsonFolder = sharedDict['jsonFolder']

  videoDbManager = VideoDbManager(config)
  videoDbManager.setupFolders(dbFolder, jsonFolder)
  videoDbManager.setupVideoFrameReader(videoFileName)
  videoDbManager.setupPrototxt(newPrototxtFile, deviceId)
  videoDbManager.setupQueues(producedQueue, consumedQueue)
  # finally start producing
  videoDbManager.startVideoDb(frmStrt, frmStp)

def runVideoCaffeManager(sharedDict, producedQueue, consumedQueue, \
  postProcessQueue, deviceId, newPrototxtFile):
  """Run single videoCaffeManager process"""
  maxProducedQueueSize = sharedDict['maxProducedQueueSize']
  
  logging.info("Waiting for videoDb queue to grow before starting VideoCaffeManager for deviceId %d" % deviceId)
  while producedQueue.qsize() < maxProducedQueueSize:
    time.sleep(5)

  logging.info("VideoCaffeManager process for deviceId %d started" % deviceId)
  videoCaffeManager = VideoCaffeManager(config)
  videoCaffeManager.setupNet(newPrototxtFile, deviceId)
  videoCaffeManager.setupQueues(producedQueue, consumedQueue, postProcessQueue)
  # finally start consuming
  videoCaffeManager.startForwards()

class VideoProcessThread( object ):
  """Class responsible for starting and running caffe on video"""
  def __init__(self, configFileName, videoFileName, baseDbFolder, jsonFolder, numpyFolder):
    """Initialize values"""
    self.configFileName = configFileName
    self.videoFileName = videoFileName
    logging.basicConfig(
      format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=logging.INFO, datefmt="%Y-%m-%d--%H:%M:%S"
      )

    global config 
    config = Config(configFileName)
    self.config = config
    self.runCaffe = self.config.ci_runCaffe
    self.runPostProcessor = self.config.ci_runPostProcess
    self.frameStartNumber = self.config.ci_videoFrameNumberStart

    # Folder to save files
    self.baseDbFolder = baseDbFolder
    self.jsonFolder = jsonFolder
    self.numpyFolder = numpyFolder
    Config.rm_rf(self.baseDbFolder)
    Config.mkdir_p(self.baseDbFolder)
    Config.mkdir_p(self.jsonFolder)
    Config.mkdir_p(self.numpyFolder)
    # Logging levels
    logging.basicConfig(
      format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=self.config.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

    # More than 1 GPU Available?
    self.gpu_devices = self.config.ci_gpu_devices
    self.version = LogoVersion()

    self.maxProducedQueueSize = self.config.ci_lmdbBufferMaxSize
    self.maxConsumedQueueSize = \
        self.config.ci_lmdbBufferMaxSize - self.config.ci_lmdbBufferMinSize
    if self.maxConsumedQueueSize <= 0:
      raise RuntimeError("LMDB buffer min size must be smaller than lmdb buffer max size")
    self.logIntervalSeconds = self.config.logIntervalSeconds

  def run( self ):
    """Run the video through caffe"""
    videoTimeLengthSeconds = 0
    videoFrameReader = None

    self.version.logVersion()
    if self.runCaffe:
      logging.info("Setting up caffe run for video %s" % self.videoFileName)
    if self.runPostProcessor:
      logging.info("Setting up post-processing to run in parallel")

    # Share state with other processes - since objects need to be pickled
    # only put primitives where possible
    sharedManager = Manager()
    sharedDict = sharedManager.dict()
    sharedDict['videoFileName'] = self.videoFileName
    sharedDict['jsonFolder'] = self.jsonFolder
    sharedDict['numpyFolder'] = self.numpyFolder
    sharedDict['maxProducedQueueSize'] = self.maxProducedQueueSize

    # ----------------------
    # PROCESSING IN GPU
    # ----------------------
    producedQueues = OrderedDict()
    consumedQueues = OrderedDict()
    videoDbManagerProcesses = []
    videoCaffeManagerProcesses = []
    postProcessQueue = JoinableQueue()
    results = multiprocessing.Queue()

    myPostProcessPipeline = Pipeline( [
                              CaffeResultPostProcess( self.config, None )
                            ], postProcessQueue, results )
    myPostProcessPipeline.start()

    startTime = time.time()
    if self.runCaffe:
      # get length of video
      videoFrameReader = VideoFrameReader(self.videoFileName)
      videoTimeLengthSeconds = videoFrameReader.getLengthInMicroSeconds() * 1.0/1000000
      # Calculate frameStep from density and fps
      self.frameStep = int( round ( ( 1.0 * videoFrameReader.fps )/self.config.sw_frame_density) ) 
      logging.info( "Frame Step will be %s, as fps is: %s and density is %s"
          % ( self.frameStep, videoFrameReader.fps, self.config.sw_frame_density ) )

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
            postProcessQueue, deviceId, newPrototxtFile))
        videoCaffeManagerProcesses += [videoCaffeManagerProcess]
        videoCaffeManagerProcess.start()
        deviceCount += 1

    # closing videoFrameReader might take a while - so last statment prior to joining
    if self.runCaffe:
      videoFrameReader.close()


    # ----------------------
    # PROCESS MANAGEMENT
    # ----------------------

    # join caffe threads
    if self.runCaffe:
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
        producedQueues[deviceId].join()
        consumedQueues[deviceId].join()
      logging.debug("Processing queues joined")
      logging.info("Finished scoring video")

    # clean up db folder
    Config.rm_rf(self.baseDbFolder)
    endTime = time.time()
    logging.info( 'It took VideoProcessThread %s seconds to complete' % ( endTime - startTime ) )
    # Add a poison pill for each PostProcessWorker
    num_consumers = multiprocessing.cpu_count()
    for i in xrange(num_consumers):
        postProcessQueue.put(None)
    
    # Wait for all of the inputs to finish
    myPostProcessPipeline.join()
    postProcessQueue.join()


    # print runtime as multiple of video length
    if self.runCaffe:
      multiFactor = (endTime - startTime) / videoTimeLengthSeconds
      logging.info( 'The total runtime was (%0.2f x) of video length (%0.2f seconds)' % \
        (multiFactor, videoTimeLengthSeconds))
