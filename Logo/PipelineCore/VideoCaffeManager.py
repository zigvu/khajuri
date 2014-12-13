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

  def setupNet(self, newPrototxtFile, deviceId):
    """Setup caffe network"""
    # initializes the following:
    self.caffe_net = None
    self.deviceId = deviceId

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

  def setupQueues(self, producedQueue, consumedQueue, deviceId):
    """Setup queues"""
    self.producedQueue = producedQueue
    self.consumedQueue = consumedQueue
    self.deviceId = deviceId

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
      logging.info("Caffe working on batch %s on device %d" % (dbBatchMappingFile, self.deviceId))
      self.forward()
      # once scores are saved, put it in deletion queue
      self.consumedQueue.put(dbBatchMappingFile)
      self.producedQueue.task_done()
    logging.info("Caffe finished working all batches on device %d" % (self.deviceId))

  def forward(self):
    """Forward call in caffe"""
    logging.info("producedQueue size: %d, deviceId: %d" % (self.producedQueue.qsize(), self.deviceId))
    logging.info("consumedQueue size: %d, deviceId: %d" % (self.consumedQueue.qsize(), self.deviceId))
    time.sleep(1)
