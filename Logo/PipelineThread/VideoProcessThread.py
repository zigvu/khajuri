import os, time
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


def runLogConsolidator(logQueue):
  """Consolidate log from multiple processes"""
  logConsolidator = LogConsolidator(config)
  logConsolidator.setupQueues(logQueue)
  # finally start log consolidation
  logConsolidator.startConsolidation()


class VideoProcessThread(object):
  """Class responsible for starting and running caffe on video"""

  def __init__(self, configFileName, videoFileName, \
    baseDbFolder, jsonFolder, numpyFolder, videoId, chiaVersionId):
    """Initialize values"""
    self.configFileName = configFileName
    self.videoFileName = videoFileName
    self.videoId = videoId
    self.chiaVersionId = chiaVersionId

    global config
    config = Config(configFileName)
    self.config = config

    # Logging infrastructure
    self.logQueue = self.config.logQueue
    self.logConsolidatorProcess = Process(
        target=runLogConsolidator, args=(self.logQueue,))
    self.logConsolidatorProcess.start()

    self.logger = self.config.logger
    branch, commit = Version().getGitVersion()
    self.logger.info('Branch: %s' % branch)
    self.logger.info('Commit: %s' % commit)

    self.status = Status(self.logger)

    self.runCaffe = self.config.ci_runCaffe
    self.runPostProcessor = self.config.ci_runPostProcess
    self.frameStartNumber = self.config.ci_videoFrameNumberStart

    # Folder to save files
    self.baseDbFolder = baseDbFolder
    self.jsonFolder = jsonFolder
    self.numpyFolder = numpyFolder
    Config.rm_rf(self.baseDbFolder)
    Config.mkdir_p(self.baseDbFolder)

    # if JSON writer is enabled
    if self.config.pp_resultWriterJSON:
      Config.mkdir_p(self.jsonFolder)
      Config.mkdir_p(self.numpyFolder)

    if self.config.pp_resultWriterRabbit:
      # TODO: find a better way
      # For now, tag along variables in config
      self.config.videoId = videoId
      self.config.chiaVersionId = chiaVersionId

    # More than 1 GPU Available?
    self.gpu_devices = self.config.ci_gpu_devices

    self.maxProducedQueueSize = self.config.ci_lmdbBufferMaxSize
    self.maxConsumedQueueSize = \
        self.config.ci_lmdbBufferMaxSize - self.config.ci_lmdbBufferMinSize
    if self.maxConsumedQueueSize <= 0:
      raise RuntimeError(
          "LMDB buffer min size must be smaller than lmdb buffer max size")

  def run(self):
    """Run the video through caffe"""
    videoTimeLengthSeconds = 0
    videoFrameReader = None

    if self.runCaffe:
      self.logger.info("Setting up caffe run for video %s" % self.videoFileName)
    if self.runPostProcessor:
      self.logger.info("Setting up post-processing to run in parallel")
    if config.pp_resultWriterJSON:
      self.logger.info("Writing output to JSON files")
    if config.pp_resultWriterRabbit:
      self.logger.info("Writing output to RabbitMq")
      amqp_url = self.config.mes_amqp_url
      serverQueueName = self.config.mes_q_vm2_kahjuri_development_video_data
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
    resultsQueue = multiprocessing.Queue()

    myPostProcessPipeline = Pipeline(
        [CaffeResultPostProcess(self.config, self.status)], postProcessQueue,
        resultsQueue)
    myPostProcessPipeline.start()

    startTime = time.time()
    if self.runCaffe:
      # get length of video
      videoFrameReader = VideoFrameReader(self.videoFileName)
      videoTimeLengthSeconds = videoFrameReader.getLengthInMicroSeconds() * \
          1.0 / 1000000
      # Calculate frameStep from density and fps
      self.frameStep = int(round(
          (1.0 * videoFrameReader.fps) / self.config.sw_frame_density))
      self.logger.info(
          "FPS: %s, FrameDensity: %s, FrameStep: %s" % (
              videoFrameReader.fps, self.config.sw_frame_density, self.frameStep
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
    Config.rm_rf(self.baseDbFolder)

    # Add a poison pill for each PostProcessWorker
    num_consumers = multiprocessing.cpu_count()
    for i in xrange(num_consumers):
      postProcessQueue.put(None)

    # Wait for all of the inputs to finish
    myPostProcessPipeline.join()
    postProcessQueue.join()

    # Inform rabbit writer that this video processing has completed
    if config.pp_resultWriterRabbit:
      amqp_url = self.config.mes_amqp_url
      serverQueueName = self.config.mes_q_vm2_kahjuri_development_video_data
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
      multiFactor = (endTime - startTime) / videoTimeLengthSeconds
      self.logger.info(
          'The total runtime was (%0.2f x) of video length (%0.2f seconds)' %
          (multiFactor, videoTimeLengthSeconds))

    # join logging queue
    self.logQueue.put(None)
    self.logQueue.join()
    self.logConsolidatorProcess.join()
