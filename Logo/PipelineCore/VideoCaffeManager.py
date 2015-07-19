import time
import json
from collections import OrderedDict

import caffe

from config.Config import Config
from config.Status import Status

from postprocessing.type.Frame import Frame
from postprocessing.task.JsonWriter import JsonWriter


class VideoCaffeManager(object):
  """Class for running patches through Caffe"""

  def __init__(self, config):
    """Initialization"""
    self.config = config
    self.logger = self.config.logging.logger
    self.machineCfg = self.config.machine
    self.caffeInputCfg = self.config.caffeInput

    self.status = Status(self.logger)

    self.classes = self.caffeInputCfg.ci_allClassIds
    self.numOfClasses = len(self.classes)
    self.runPostProcessor = self.caffeInputCfg.ci_runPostProcess
    self.patchMapping = self.config.allCellBoundariesDict["patchMapping"]
    self.totalPatches = len(self.patchMapping)

    # manage post-process queue size
    self.ppQueue_highWatermark = self.caffeInputCfg.ci_ppQueue_highWatermark
    self.ppQueue_lowWatermark = self.caffeInputCfg.ci_ppQueue_lowWatermark
    self.ppQueue_isAboveHighWatermark = False
    self.postProcessQueueSleepTime = 10


  def setupNet(self, newPrototxtFile, deviceId):
    """Setup caffe network"""
    # initializes the following:
    self.caffe_net = None
    self.deviceId = deviceId
    self.caffeBatchSize = None

    # read batch size from proto file
    with open(newPrototxtFile) as fread:
      lines = fread.readlines()
      for line in lines:
        if "batch_size:" in line:
          self.caffeBatchSize = int(line.strip(" \n").split("batch_size: ")[1])
    if self.caffeBatchSize == None:
      raise RuntimeError(
          "Couldn't read batch size from file %s" % newPrototxtFile)

    self.logger.info("DeviceId: %d: Setup caffe network" % self.deviceId)
    useGPU = self.machineCfg.useGPU()
    modelFile = self.caffeInputCfg.ci_modelFile

    # HACK: without reinitializing caffe_net twice, it won't give reproducible results
    # Seems to happen in both CPU and GPU runs:
    self.caffe_net = caffe.Net(newPrototxtFile, modelFile)
    self.caffe_net.set_phase_test()
    if useGPU:
      self.caffe_net.set_mode_gpu()
      self.caffe_net.set_device(self.deviceId)
    else:
      self.caffe_net.set_mode_cpu()
    self.logger.debug("DeviceId: %d: Reinitializing caffe_net" % self.deviceId)

    self.caffe_net = caffe.Net(newPrototxtFile, modelFile)
    self.caffe_net.set_phase_test()
    if useGPU:
      self.caffe_net.set_mode_gpu()
      self.caffe_net.set_device(self.deviceId)
    else:
      self.caffe_net.set_mode_cpu()
    self.logger.debug("DeviceId: %d: Done initializing caffe_net" % self.deviceId)

  def setupQueues(self, producedQueue, consumedQueue, postProcessQueue):
    """Setup queues"""
    self.producedQueue = producedQueue
    self.consumedQueue = consumedQueue
    self.postProcessQueue = postProcessQueue

  def startForwards(self):
    """Timing caffe forward calls"""
    while True:
      dbBatchMappingFile = self.producedQueue.get()
      # producer finished producing
      if dbBatchMappingFile is None:
        self.consumedQueue.put(None)
        self.producedQueue.task_done()
        # poison pill means done with evaluations
        break
      # producer is not finished producing, so consume
      self.logger.debug(
          "DeviceId: %d: Caffe working on batch %s" % 
          (self.deviceId, dbBatchMappingFile))
      self.forward(dbBatchMappingFile)
      # once scores are saved, put it in deletion queue
      self.consumedQueue.put(dbBatchMappingFile)
      self.producedQueue.task_done()
      self.pauseForPostProcessQueue()
    self.logger.info("DeviceId: %d: Caffe finished all batches" % self.deviceId)

  def forward(self, dbBatchMappingFile):
    """Forward call in caffe"""
    # Read mapping and json output files
    dbBatchMapping = json.load(open(dbBatchMappingFile, "r"))
    frames = OrderedDict()
    maxPatchCounter = 0

    for patchCounter, infoDict in dbBatchMapping.iteritems():
      if maxPatchCounter < int(patchCounter):
        maxPatchCounter = int(patchCounter)
      jsonFile = infoDict['jsonFile']
      if jsonFile not in frames.keys():
        frames[jsonFile] = Frame(
            self.classes, self.totalPatches, self.caffeInputCfg.ci_scoreTypes.keys())
        frames[jsonFile].filename = jsonFile
        frames[jsonFile].frameNumber = infoDict['frameNum']
        frames[jsonFile].frameDisplayTime = 0

    # We do ONLY ONE forward pass - we expect to get only 1 batch of data
    # (which of course could be configured to do multiple frames)

    # we start our patch counting from label equals to one batch size minus 
    # the maxPatchCounter
    patchCounter = maxPatchCounter - self.caffeBatchSize + 1
    if patchCounter < 0:
      patchCounter = 0

    output = self.caffe_net.forward()
    probablities = output['prob']
    probablities_fc8 = self.caffe_net.blobs['fc8_logo'].data
    for k in range(0, output['label'].size):
      printStr = ""
      scores = probablities[k, :, 0, 0]
      scores_fc8 = probablities_fc8[k, :, 0, 0]
      # Note: if number of patches is not multiple of batch size, then caffe
      #  displays results for patches in the begining of db
      if patchCounter <= maxPatchCounter:
        curPatchNumber = int(output['label'].item(k))
        # Add scores to json
        infoDict = dbBatchMapping[str(curPatchNumber)]
        frames[infoDict['jsonFile']].addScores(infoDict['patchNum'], scores)
        frames[infoDict['jsonFile']].addfc8Scores(
            infoDict['patchNum'], scores_fc8)
        # self.logger.debug("%s" % printStr)
      patchCounter += 1

    # Save and put json files in post processing queue
    for jsonFile, frame in frames.iteritems():
      if self.runPostProcessor:
        self.postProcessQueue.put((frame, self.classes))
      else:
        JsonWriter(self.config, self.status)((frame, self.classes))

  def pauseForPostProcessQueue(self):
    """In case post-process queue is too big, pause"""
    # only run if post-processing is enabled
    if not self.runPostProcessor:
      return
    # get queue size
    ppQueue_curSize = self.postProcessQueue.qsize()
    if self.ppQueue_isAboveHighWatermark:
      # if above high watermark, wait until we are below low watermark
      while ppQueue_curSize > self.ppQueue_lowWatermark:
        self.logger.debug(
            "DeviceId: %d: Waiting for pp queue to shrink" % self.deviceId)
        time.sleep(self.postProcessQueueSleepTime)
        ppQueue_curSize = self.postProcessQueue.qsize()
      # reset
      self.ppQueue_isAboveHighWatermark = False
    else:
      # mark if we go above high water mark
      if ppQueue_curSize > self.ppQueue_highWatermark:
        self.logger.debug(
            "DeviceId: %d: Above pp queue high watermark" % self.deviceId)
        self.ppQueue_isAboveHighWatermark = True
    