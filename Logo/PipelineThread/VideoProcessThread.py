import os, time, sys, glob
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager
from collections import OrderedDict
import json, pickle
import logging

import VideoReader

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.VideoFrameReader import VideoFrameReader

from Logo.PipelineCore.VideoDbManager import VideoDbManager
from Logo.PipelineCore.VideoCaffeManager import VideoCaffeManager
from Logo.PipelineCore.PostProcessManager import PostProcessManager
from Logo.PipelineCore.Version import LogoVersion


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
  postProcessQueue, deviceId, newPrototxtFile):
  """Run single videoCaffeManager process"""
  configFileName = sharedDict['configFileName']
  maxProducedQueueSize = sharedDict['maxProducedQueueSize']
  
  logging.info("Waiting for videoDb queue to grow before starting VideoCaffeManager for deviceId %d" % deviceId)
  while producedQueue.qsize() < maxProducedQueueSize:
    time.sleep(5)

  logging.info("VideoCaffeManager process for deviceId %d started" % deviceId)
  videoCaffeManager = VideoCaffeManager(configFileName)
  videoCaffeManager.setupNet(newPrototxtFile, deviceId)
  videoCaffeManager.setupQueues(producedQueue, consumedQueue, postProcessQueue)
  # finally start consuming
  videoCaffeManager.startForwards()

def runFramePostProcess(sharedDict, postProcessQueue):
  """Run post processing on raw score JSON files"""
  configFileName = sharedDict['configFileName']
  numpyFolder = sharedDict['numpyFolder']

  imageWidth = sharedDict['imageWidth']
  imageHeight = sharedDict['imageHeight']
  allCellBoundariesDict = sharedDict['allCellBoundariesDict']

  postProcessManager = PostProcessManager(configFileName)
  postProcessManager.setupFolders(numpyFolder)
  postProcessManager.setupCells(imageWidth, imageHeight, allCellBoundariesDict)
  postProcessManager.setupQueues(postProcessQueue)
  # finally start processing
  postProcessManager.startPostProcess()


class VideoProcessThread( object ):
  """Class responsible for starting and running caffe on video"""
  def __init__(self, configFileName, videoFileName, baseDbFolder, jsonFolder, numpyFolder):
    """Initialize values"""
    self.configFileName = configFileName
    self.videoFileName = videoFileName

    self.configReader = ConfigReader(configFileName)
    self.runCaffe = self.configReader.ci_runCaffe
    self.runPostProcessor = self.configReader.ci_runPostProcess
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
    logging.basicConfig(
      format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=self.configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

    # More than 1 GPU Available?
    self.gpu_devices = self.configReader.ci_gpu_devices
    self.version = LogoVersion()

    self.maxProducedQueueSize = self.configReader.ci_lmdbBufferMaxSize
    self.maxConsumedQueueSize = \
        self.configReader.ci_lmdbBufferMaxSize - self.configReader.ci_lmdbBufferMinSize
    if self.maxConsumedQueueSize <= 0:
      raise RuntimeError("LMDB buffer min size must be smaller than lmdb buffer max size")
    self.logIntervalSeconds = self.configReader.logIntervalSeconds

  def run( self ):
    """Run the video through caffe"""
    startTime = time.time()
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
    sharedDict['configFileName'] = self.configFileName
    sharedDict['videoFileName'] = self.videoFileName
    sharedDict['jsonFolder'] = self.jsonFolder
    sharedDict['numpyFolder'] = self.numpyFolder
    sharedDict['maxProducedQueueSize'] = self.maxProducedQueueSize

    # ----------------------
    # PROCESSING IN GPU
    producedQueues = OrderedDict()
    consumedQueues = OrderedDict()
    videoDbManagerProcesses = []
    videoCaffeManagerProcesses = []
    postProcessQueue = JoinableQueue()

    if self.runCaffe:
      # get length of video
      videoFrameReader = VideoFrameReader(self.videoFileName)
      videoTimeLengthSeconds = videoFrameReader.getLengthInMicroSeconds() * 1.0/1000000
      # Calculate frameStep from density and fps
      self.frameStep = int( round ( ( 1.0 * videoFrameReader.fps )/self.configReader.sw_frame_density) ) 
      logging.info( "Frame Step will be %s, as fps is: %s and density is %s"
          % ( self.frameStep, videoFrameReader.fps, self.configReader.sw_frame_density ) )

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

    # ----------------------
    # POST-PROCESSING IN CPU
    framePostProcesses = []
    num_consumers = 0
    if self.runPostProcessor:
      jsonFiles = []
      imageWidth = None
      imageHeight = None

      # if caffe was not run, we are reading from folder instead    
      if self.runCaffe:
        # image width/height needed for cell boundaries
        imageWidth = videoFrameReader.getImageDim().width
        imageHeight = videoFrameReader.getImageDim().height
      else:
        jsonFiles = glob.glob(os.path.join(self.jsonFolder, "*json"))
        jsonReaderWriter = JSONReaderWriter(jsonFiles[0])
        imageWidth = jsonReaderWriter.getFrameWidth()
        imageHeight = jsonReaderWriter.getFrameHeight()
        # Put JSON in queue so that workers can consume
        for jsonFileName in jsonFiles:
          logging.debug("Putting JSON file in queue: %s" % os.path.basename(jsonFileName))
          postProcessQueue.put(jsonFileName)

      # cell boundary computation can be expensive so share
      # assume that the data structure is simple pickalable dict
      allCellBoundariesDict = PostProcessManager.getAllCellBoundariesDict(\
        self.configReader, imageWidth, imageHeight)
      sharedDict['allCellBoundariesDict'] = allCellBoundariesDict
      sharedDict['imageWidth'] = imageWidth
      sharedDict['imageHeight'] = imageHeight

      # start threads
      num_consumers = max(int(self.configReader.multipleOfCPUCount * multiprocessing.cpu_count()), 1)
      #num_consumers = 1
      for i in xrange(num_consumers):
        framePostProcess = Process(\
          target=runFramePostProcess,\
          args=(sharedDict, postProcessQueue))
        framePostProcesses += [framePostProcess]
        framePostProcess.start()

      if not self.runCaffe:
        # print progress
        while postProcessQueue.qsize() > 1:
          logging.info("Post processing %d percent done" % (int(100 - \
            100.0 * postProcessQueue.qsize()/len(jsonFiles))))
          time.sleep(self.logIntervalSeconds)
      # end run post-processor

    # closing videoFrameReader might take a while - so last statment prior to joining
    if self.runCaffe:
      videoFrameReader.close()

    # ----------------------
    # PROCESS MANAGEMENT

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

    # join post-processing threads
    if self.runPostProcessor:
      logging.info("Waiting for post-processes to complete")
      for i in xrange(num_consumers):
        postProcessQueue.put(None)
      postProcessQueue.join()
      logging.debug("Post processing queues joined")
      for framePostProcess in framePostProcesses:
        framePostProcess.join()
      logging.debug("Post processing process joined")      
      logging.info("All post-processing tasks complete")

    # clean up db folder
    ConfigReader.rm_rf(self.baseDbFolder)

    endTime = time.time()
    logging.info( 'It took VideoProcessThread %s seconds to complete' % ( endTime - startTime ) )

    # print runtime as multiple of video length
    if self.runCaffe:
      multiFactor = (endTime - startTime) / videoTimeLengthSeconds
      logging.info( 'The runtime was (%0.2f x) of video length (%0.2f seconds)' % \
        (multiFactor, videoTimeLengthSeconds))
      
