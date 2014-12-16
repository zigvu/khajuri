import os, shutil, re, time
import json, math
from collections import OrderedDict
import logging

import caffe
from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter

class VideoCaffeManager( object ):
  """Class for running patches through Caffe"""
  def __init__(self, configFileName):
    self.configReader = ConfigReader(configFileName)
    self.classes = self.configReader.ci_allClassIds
    self.numOfClasses = len(self.classes)


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
      raise RuntimeError("Couldn't read batch size from file %s" % newPrototxtFile)

    logging.debug("Setup caffe network for device id %d" % self.deviceId)
    useGPU = self.configReader.ci_useGPU
    modelFile = self.configReader.ci_modelFile

    # HACK: without reinitializing caffe_net twice, it won't give reproducible results
    # Seems to happen in both CPU and GPU runs:
    self.caffe_net = caffe.Net(newPrototxtFile, modelFile)
    self.caffe_net.set_phase_test() 
    if useGPU:
      self.caffe_net.set_mode_gpu()
      self.caffe_net.set_device( self.deviceId )
    else:
      self.caffe_net.set_mode_cpu()
    logging.debug("Reinitializing caffe_net")

    self.caffe_net = caffe.Net(newPrototxtFile, modelFile)
    self.caffe_net.set_phase_test() 
    if useGPU:
      self.caffe_net.set_mode_gpu()
      self.caffe_net.set_device( self.deviceId )
    else:
      self.caffe_net.set_mode_cpu()
    logging.info("Done initializing caffe_net")

  def setupQueues(self, producedQueue, consumedQueue):
    """Setup queues"""
    self.producedQueue = producedQueue
    self.consumedQueue = consumedQueue

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
      logging.debug("Caffe working on batch %s on device %d" % (dbBatchMappingFile, self.deviceId))
      self.forward(dbBatchMappingFile)
      # once scores are saved, put it in deletion queue
      self.consumedQueue.put(dbBatchMappingFile)
      self.producedQueue.task_done()
    logging.info("Caffe finished working all batches on device %d" % (self.deviceId))

  def forward(self, dbBatchMappingFile):
    """Forward call in caffe"""
    logging.debug("Queues: producedQueue: %d, deviceId: %d" % (self.producedQueue.qsize(), self.deviceId))
    logging.debug("Queues: consumedQueue: %d, deviceId: %d" % (self.consumedQueue.qsize(), self.deviceId))

    # Read mapping and json output files
    dbBatchMapping = json.load(open(dbBatchMappingFile, "r"))
    jsonFiles = []
    jsonRWs = OrderedDict()
    maxPatchCounter = 0

    for patchCounter, jsonFile in dbBatchMapping.iteritems():
      if maxPatchCounter < int(patchCounter):
        maxPatchCounter = int(patchCounter)
      if jsonFile not in jsonFiles:
        jsonFiles += [jsonFile]
        jsonRWs[jsonFile] = JSONReaderWriter(jsonFile)

    # We do ONLY ONE forward pass - we expect to get only 1 batch of data
    # (which of course could be configured to do multiple frames)

    # we start our patch counting from label equals to one batch size minus the maxPatchCounter
    patchCounter = maxPatchCounter - self.caffeBatchSize + 1
    if patchCounter < 0:
      patchCounter = 0

    output = self.caffe_net.forward()
    probablities = output['prob']
    for k in range(0, output['label'].size):
      printStr = ""
      scores = {}
      for j in range(0, self.numOfClasses):
        scores[self.classes[j]] = probablities[k][j].item(0)
        printStr = "%s,%f" % (printStr, scores[self.classes[j]])
      # Note: if number of patches is not multiple of batch size, then caffe
      #  displays results for patches in the begining of leveldb
      if patchCounter <= maxPatchCounter:
        curPatchNumber = int(output['label'].item(k))
        printStr = "%s%s" % (dbBatchMapping[str(curPatchNumber)], printStr)
        # Add scores to json
        jsonRWs[dbBatchMapping[str(curPatchNumber)]].addScores(curPatchNumber, scores)
        # logging.debug("%s" % printStr)
      patchCounter += 1

    # Save and put json files in post processing queue
    for jsonFile, jsonRW in jsonRWs.iteritems():
      jsonRW.saveState()
      # TODO: put in processing queue
