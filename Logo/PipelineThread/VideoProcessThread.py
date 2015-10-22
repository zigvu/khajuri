import os
import time
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager
from collections import OrderedDict
import json

import VideoReader

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.VideoDbManager import VideoDbManager
from Logo.PipelineCore.VideoCaffeManager import VideoCaffeManager
from Logo.PipelineCore.LogConsolidator import LogConsolidator

from config.Config import Config
from config.Version import Version
from config.Status import Status
from config.Utils import Utils

from postprocessing.task.CaffeResultPostProcess import CaffeResultPostProcess

from infra.Pipeline import Pipeline

from messaging.infra.Pickler import Pickler
from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient

config = None


def runVideoDbManager(sharedDict, producedQueue, consumedQueue, \
  deviceId, frmStrt, frmStp, dbFolder, newPrototxtFile):
  """Run single videoDBManager process"""
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

  while producedQueue.qsize() < maxProducedQueueSize:
    time.sleep(5)

  videoCaffeManager = VideoCaffeManager(config)
  videoCaffeManager.setupNet(newPrototxtFile, deviceId)
  videoCaffeManager.setupQueues(producedQueue, consumedQueue, postProcessQueue)
  # finally start consuming
  videoCaffeManager.startForwards()


def runLogConsolidator():
  """Consolidate log from multiple processes"""
  logConsolidator = LogConsolidator(config)
  # finally start log consolidation
  logConsolidator.startConsolidation()


class VideoProcessThread(object):
  """Class responsible for starting and running caffe on video"""

  def __init__(self, configFileName):
    """Initialize values"""
    global config
    config = Config(configFileName)
    self.config = config

    self.loggingCfg = self.config.logging
    self.jobCfg = self.config.job
    self.slidingWindowCfg = self.config.slidingWindow
    self.caffeInputCfg = self.config.caffeInput
    self.postProcessingCfg = self.config.postProcessing
    self.storageCfg = self.config.storage
    self.machineCfg = self.config.machine
    self.messagingCfg = self.config.messaging

    # Logging infrastructure
    self.logQueue = self.loggingCfg.logQueue
    self.logConsolidatorProcess = Process(
        target=runLogConsolidator, args=())
    self.logConsolidatorProcess.start()

    self.logger = self.loggingCfg.logger
    branch, commit = Version().getGitVersion()
    self.logger.info('Branch: %s' % branch)
    self.logger.info('Commit: %s' % commit)

    self.status = Status(self.logger)

    # job details
    self.videoId = self.jobCfg.videoId
    self.videoFileName = self.jobCfg.videoFileName
    self.chiaVersionId = self.jobCfg.chiaVersionId

    self.runCaffe = self.caffeInputCfg.ci_runCaffe
    self.runPostProcessor = self.caffeInputCfg.ci_runPostProcess
    self.frameStartNumber = self.caffeInputCfg.ci_videoFrameNumberStart

    # Folder to save files
    self.baseDbFolder = self.storageCfg.baseDbFolder
    self.jsonFolder = self.storageCfg.jsonFolder
    Utils.rm_rf(self.baseDbFolder)
    Utils.mkdir_p(self.baseDbFolder)

    # if JSON writer is enabled
    if self.storageCfg.enableJsonReadWrite:
      Utils.mkdir_p(self.jsonFolder)

    # More than 1 GPU Available?
    self.gpu_devices = self.machineCfg.gpuDevices

    self.maxProducedQueueSize = self.caffeInputCfg.ci_lmdbBufferMaxSize
    self.maxConsumedQueueSize = \
        self.caffeInputCfg.ci_lmdbBufferMaxSize - \
        self.caffeInputCfg.ci_lmdbBufferMinSize
    if self.maxConsumedQueueSize <= 0:
      raise RuntimeError(
          "LMDB buffer min size must be smaller than lmdb buffer max size")

    # max size of post-process queue
    self.maxPostProcessQueueSize = self.caffeInputCfg.ci_ppQueue_maxSize

  def run(self):
    """Run the video through caffe"""
    videoFrameReader = None

    if self.runCaffe:
      self.logger.info("Setting up caffe run for video %s" % self.videoFileName)
    if self.runPostProcessor:
      self.logger.info("Setting up post-processing to run in parallel")
    if self.storageCfg.enableJsonReadWrite:
      self.logger.info("Writing output to JSON files")
    if self.storageCfg.enableHdf5ReadWrite:
      self.logger.info("Writing output to RabbitMq")
      amqp_url = self.messagingCfg.amqpURL
      serverQueueName = self.messagingCfg.queues.videoData
      self.rabbitWriter = RpcClient(amqp_url, serverQueueName)
      # inform rabbit consumer that video processing is ready to start
      message = Pickler.pickle({})
      headers = Headers.videoStorageStart(self.videoId, self.chiaVersionId)
      response = json.loads(self.rabbitWriter.call(headers, message))
      # TODO: error check
      # since finishing post-processing will take a long time, close connection
      self.rabbitWriter.close()

    # Share state with other processes - since objects need to be pickled
    # only put primitives where possible
    sharedManager = Manager()
    sharedDict = sharedManager.dict()
    sharedDict['videoFileName'] = self.videoFileName
    sharedDict['jsonFolder'] = self.jsonFolder
    sharedDict['maxProducedQueueSize'] = self.maxProducedQueueSize

    # ----------------------
    # PROCESSING IN GPU
    # ----------------------
    producedQueues = OrderedDict()
    consumedQueues = OrderedDict()
    videoDbManagerProcesses = []
    videoCaffeManagerProcesses = []
    postProcessQueue = JoinableQueue(maxsize=self.maxPostProcessQueueSize)
    resultsQueue = multiprocessing.Queue()

    myPostProcessPipeline = Pipeline(
        [CaffeResultPostProcess(self.config, self.status)], postProcessQueue,
        resultsQueue)
    myPostProcessPipeline.start()

    startTime = time.time()
    if self.runCaffe:
      videoFrameReader = VideoFrameReader(self.videoFileName)
      # Calculate frameStep from density and fps
      self.frameStep = int(round(
          (1.0 * videoFrameReader.fps) / self.slidingWindowCfg.sw_frame_density))
      self.logger.info(
          "FPS: %s, FrameDensity: %s, FrameStep: %s" % (
              videoFrameReader.fps, self.slidingWindowCfg.sw_frame_density, 
              self.frameStep
          ))

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
        newPrototxtFile = os.path.join(
            self.baseDbFolder,
            'prototxt_%s.prototxt' % os.path.basename(dbFolder))
        # patch producer - save to DB
        videoDbManagerProcess = Process(
            target=runVideoDbManager,
            args=(
                sharedDict, producedQueues[deviceId], consumedQueues[deviceId],
                deviceId, frmStrt, frmStp, dbFolder, newPrototxtFile))
        videoDbManagerProcesses += [videoDbManagerProcess]
        videoDbManagerProcess.start()

        # patch consumer - run caffe
        videoCaffeManagerProcess = Process(
            target=runVideoCaffeManager,
            args=(
                sharedDict, producedQueues[deviceId], consumedQueues[deviceId],
                postProcessQueue, deviceId, newPrototxtFile))
        videoCaffeManagerProcesses += [videoCaffeManagerProcess]
        videoCaffeManagerProcess.start()
        deviceCount += 1

    # closing videoFrameReader might take a while
    # so last statment prior to joining
    if self.runCaffe:
      videoFrameReader.close()

    # ----------------------
    # PROCESS MANAGEMENT
    # ----------------------

    # join caffe threads
    if self.runCaffe:
      self.logger.info("Waiting for videoDbManagerProcess process to complete.")
      for videoDbManagerProcess in videoDbManagerProcesses:
        videoDbManagerProcess.join()
      self.logger.debug("videoDbManagerProcess process joined")

      self.logger.info("Waiting for videoCaffeManagerProcess process to complete.")
      for videoCaffeManagerProcess in videoCaffeManagerProcesses:
        videoCaffeManagerProcess.join()
      self.logger.debug("videoCaffeManagerProcess process joined")

      self.logger.info("Waiting for all queues to get joined")
      for deviceId in self.gpu_devices:
        producedQueues[deviceId].join()
        consumedQueues[deviceId].join()
      self.logger.debug("Processing queues joined")
      self.logger.info("Finished scoring video")

    # clean up db folder
    Utils.rm_rf(self.baseDbFolder)

    # Add a poison pill for each PostProcessWorker
    num_consumers = multiprocessing.cpu_count()
    for i in xrange(num_consumers):
      postProcessQueue.put(None)

    # Wait for all of the inputs to finish
    myPostProcessPipeline.join()
    postProcessQueue.join()

    # Inform rabbit writer that this video processing has completed
    if self.storageCfg.enableHdf5ReadWrite:
      amqp_url = self.messagingCfg.amqpURL
      serverQueueName = self.messagingCfg.queues.videoData
      self.rabbitWriter = RpcClient(amqp_url, serverQueueName)
      message = Pickler.pickle({})
      headers = Headers.videoStorageEnd(self.videoId, self.chiaVersionId)
      response = json.loads(self.rabbitWriter.call(headers, message))
      self.rabbitWriter.close()
      self.logger.info("Finished writing output to RabbitMq")

    endTime = time.time()
    self.logger.info(
        'It took VideoProcessThread %s seconds to complete' %
        (endTime - startTime))

    # print runtime as multiple of video length
    if self.runCaffe:
      videoLengthSeconds = VideoFrameReader.getLengthInSeconds(self.videoFileName)
      multiFactor = (endTime - startTime) / videoLengthSeconds
      self.logger.info(
          'The total runtime was (%0.2f x) of video length (%0.2f seconds)' %
          (multiFactor, videoLengthSeconds))

    # join logging queue
    self.logQueue.put(None)
    self.logQueue.join()
    self.logConsolidatorProcess.join()
