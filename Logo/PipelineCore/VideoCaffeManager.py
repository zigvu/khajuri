import os, shutil, re, time
import json, math
from collections import OrderedDict
import logging

import caffe
from postprocessing.type.Frame import Frame
from postprocessing.task.JsonWriter import JsonWriter
from config.Config import Config

class VideoCaffeManager( object ):
  """Class for running patches through Caffe"""
  def __init__(self, config):
    self.config = config
    self.classes = self.config.ci_allClassIds
    self.numOfClasses = len(self.classes)
    self.runPostProcessor = self.config.ci_runPostProcess
    self.compressedJSON = self.config.pp_compressedJSON
    self.patchMapping = self.config.allCellBoundariesDict[ "patchMapping" ]
    self.totalPatches = len ( self.patchMapping )


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

    logging.info("Setup caffe network for device id %d" % self.deviceId)
    useGPU = self.config.ci_useGPU
    modelFile = self.config.ci_modelFile

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
    logging.debug("Done initializing caffe_net")

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
      logging.debug("Caffe working on batch %s on device %d" % (dbBatchMappingFile, self.deviceId))
      self.forward(dbBatchMappingFile)
      # once scores are saved, put it in deletion queue
      self.consumedQueue.put(dbBatchMappingFile)
      self.producedQueue.task_done()
    logging.info("Caffe finished working all batches on device %d" % (self.deviceId))

  def forward(self, dbBatchMappingFile):
    """Forward call in caffe"""
    # Read mapping and json output files
    dbBatchMapping = json.load(open(dbBatchMappingFile, "r"))
    frames = OrderedDict()
    maxPatchCounter = 0

    for patchCounter, infoDict in dbBatchMapping.iteritems():
      if maxPatchCounter < int(patchCounter):
        maxPatchCounter = int(patchCounter)
      jsonFile = infoDict[ 'jsonFile' ]
      if jsonFile not in frames.keys():
        frames[jsonFile] = Frame( self.classes, self.totalPatches, 
                                  self.config.ci_scoreTypes.keys() )
        frames[jsonFile].filename = jsonFile
        frames[jsonFile].frameNumber = infoDict[ 'frameNum' ]
        frames[jsonFile].frameDisplayTime = 0

    # We do ONLY ONE forward pass - we expect to get only 1 batch of data
    # (which of course could be configured to do multiple frames)

    # we start our patch counting from label equals to one batch size minus the maxPatchCounter
    patchCounter = maxPatchCounter - self.caffeBatchSize + 1
    if patchCounter < 0:
      patchCounter = 0

    output = self.caffe_net.forward()
    probablities = output['prob']
    probablities_fc8 = self.caffe_net.blobs['fc8_logo'].data
    for k in range(0, output['label'].size):
      printStr = ""
      scores = {}
      scores_fc8 = {}
      scores = probablities[k].item(0)
      scores_fc8 = probablities_fc8[k].item(0)
      # print 'scores: %s, type %s, shape: %s' % ( scores, type( scores ), scores.shape )
      # Note: if number of patches is not multiple of batch size, then caffe
      #  displays results for patches in the begining of db
      if patchCounter <= maxPatchCounter:
        curPatchNumber = int(output['label'].item(k))
        printStr = "%s%s" % (dbBatchMapping[str(curPatchNumber)], printStr)
        # Add scores to json
        infoDict = dbBatchMapping[str(curPatchNumber)]
        frames[ infoDict[ 'jsonFile' ] ].addScores( infoDict[ 'patchNum' ], scores )
        frames[ infoDict[ 'jsonFile' ] ].addfc8Scores( infoDict[ 'patchNum' ], scores )
        # logging.debug("%s" % printStr)
      patchCounter += 1

    # Save and put json files in post processing queue
    for jsonFile, frame in frames.iteritems():
      if self.runPostProcessor:
        self.postProcessQueue.put(( frame, self.classes ) )
      else:
        JsonWriter( self.config, None )(( frame, self.classes ) )
