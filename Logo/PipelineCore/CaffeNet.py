import os, shutil, re, time
import json, math
from collections import OrderedDict
import logging

import caffe
from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter

class CaffeNet( object ):
  def __init__(self, configReader, deviceId):
    logging.debug("Initializing CaffeNet")
    self.prototxtFile = configReader.ci_video_prototxtFile
    self.modelFile = configReader.ci_modelFile
    self.classes = configReader.ci_allClassIds
    self.useGPU = configReader.ci_useGPU
    self.deviceId = deviceId
    self.numOfGPUs = len( configReader.ci_gpu_devices )

  def run_net(self, leveldbFolder):
    logging.info( 'Run net started' )
    caffeBatchSize = -1
    # Create new prototxt file to point to right leveldb
    prototxtWithNewLeveldb = os.path.join(os.path.dirname(leveldbFolder), \
      'prototxt_%s.prototxt' % os.path.basename(leveldbFolder))
    with open(self.prototxtFile) as fread:
      lines = fread.readlines()
    with open(prototxtWithNewLeveldb, "w") as fwrite:
      for line in lines:
        if "source:" in line:
          line = line.replace(re.findall(r'\"(.+?)\"', line)[0], leveldbFolder)
        if "batch_size:" in line:
          caffeBatchSize = int(line.strip(" \n").split("batch_size: ")[1])
        fwrite.write("%s" % line)
    if caffeBatchSize == -1:
      raise RuntimeError("Cannot determine the batch size in caffe prototxt file")
    # Read mapping and json output files
    leveldbMappingFile = os.path.join(leveldbFolder, "leveldb_mapping.json")
    leveldbMapping = json.load(open(leveldbMappingFile, "r"))
    jsonFiles = []
    jsonRWs = OrderedDict()
    maxPatchCounter = 0
    for patchCounter, jsonFile in leveldbMapping.iteritems():
      if maxPatchCounter < int(patchCounter):
        maxPatchCounter = int(patchCounter)
      if jsonFile not in jsonFiles:
        jsonFiles += [jsonFile]
        jsonRWs[jsonFile] = JSONReaderWriter(jsonFile)

    # HACK: without reinitializing caffe_net twice, it won't give reproducible results
    # Seems to happen in both CPU and GPU runs:
    logging.debug("Initializing caffe_net")
    caffe_net = caffe.Net(prototxtWithNewLeveldb, self.modelFile)
    caffe_net.set_phase_test() 
    if self.useGPU:
      caffe_net.set_mode_gpu()
      caffe_net.set_device( self.deviceId )
    else:
      caffe_net.set_mode_cpu()
    logging.debug("Reinitializing caffe_net")

    # Run caffe net
    # counter for iteration starts at 0, so increment 1 to maxPatchCounter
    numOutputIteration = int(math.ceil((maxPatchCounter + 1) * 1.0 / caffeBatchSize))
    numOfClasses = len(self.classes)
    caffe_net = caffe.Net(prototxtWithNewLeveldb, self.modelFile)
    caffe_net.set_phase_test()
    if self.useGPU:
      caffe_net.set_mode_gpu()
      caffe_net.set_device( self.deviceId )
    else:
      caffe_net.set_mode_cpu()

    # Iterate until all patches in leveldb are evaluated
    patchCounter = 0
    for i in range(0, numOutputIteration):
      output = caffe_net.forward()
      probablities = output['prob']
      for k in range(0, output['label'].size):
        printStr = ""
        scores = {}
        for j in range(0, numOfClasses):
          scores[self.classes[j]] = probablities[k][j].item(0)
          printStr = "%s,%f" % (printStr, scores[self.classes[j]])
        # Note: if number of patches is not multiple of batch size, then caffe
        #  displays results for patches in the begining of leveldb
        if patchCounter <= maxPatchCounter:
          curPatchNumber = int(output['label'].item(k))
          printStr = "%s%s" % (leveldbMapping[str(curPatchNumber)], printStr)
          # Add scores to json
          jsonRWs[leveldbMapping[str(curPatchNumber)]].addScores(curPatchNumber, scores)
          # logging.debug("%s" % printStr)
        patchCounter += 1

    # Save and put json files in post processing queue
    for jsonFile, jsonRW in jsonRWs.iteritems():
      jsonRW.saveState()

    # Clean up by deleting levedb whose use is done 
    # since large files, might need to do it twice
    ConfigReader.rm_rf(leveldbFolder)
    ConfigReader.rm_rf(prototxtWithNewLeveldb)
    ConfigReader.rm_rf(leveldbFolder)

    # Finally, return jsonFiles which were processed
    logging.info( 'Run net done.' )
    return jsonFiles
