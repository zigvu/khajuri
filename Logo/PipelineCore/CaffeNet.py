import os, shutil, re, time
import json, math
from collections import OrderedDict
import logging

import caffe
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter

class CaffeNet( object ):
  def __init__(self, configReader, postProcessQueue):
    logging.debug("Initializing CaffeNet")
    self.prototxtFile = configReader.ci_prototxtFile
    self.modelFile = configReader.ci_modelFile
    self.postProcessQueue = postProcessQueue
    self.classes = configReader.ci_allClassIds
    self.useGPU = configReader.ci_useGPU

  def run_net(self, leveldbFolder):
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
    levelDbMappingFile = os.path.join(leveldbFolder, "leveldb_mapping.json")
    levelDbMapping = json.load(open(levelDbMappingFile, "r"))
    jsonFiles = []
    jsonRWs = OrderedDict()
    maxPatchCounter = 0
    for patchCounter, jsonFile in levelDbMapping.iteritems():
      if maxPatchCounter < int(patchCounter):
        maxPatchCounter = int(patchCounter)
      if jsonFile not in jsonFiles:
        jsonFiles += [jsonFile]
        jsonRWs[jsonFile] = JSONReaderWriter(jsonFile)
    # Run caffe net
    numOutputIteration = int(math.ceil(maxPatchCounter * 1.0 / caffeBatchSize))
    numOfClasses = len(self.classes)
    caffe_net = caffe.Net(prototxtWithNewLeveldb, self.modelFile)
    caffe_net.set_phase_test()
    if self.useGPU:
      caffe_net.set_mode_gpu()
    else:
      caffe_net.set_mode_cpu()
    # Iterate until all patches in leveldb are evaluated
    for i in range(0, numOutputIteration):
      output = caffe_net.forward()
      probablities = output['prob']
      for k in range(0, output['label'].size):
        patchCounter = k + i * output['label'].size
        printStr = "%d" % (patchCounter)
        scores = {}
        for j in range(0, numOfClasses):
          scores[self.classes[j]] = probablities.item(numOfClasses * k + j)
          printStr = "%s,%f" % (printStr, scores[self.classes[j]])
        # Note: if number of patches is not multiple of batch size, then caffe
        #  displays results for patches in the begining of leveldb
        if patchCounter <= maxPatchCounter:
          # Add scores to json
          jsonRWs[levelDbMapping[str(patchCounter)]].addScores(patchCounter, scores)
          logging.debug("%s" % printStr)
    # Save and put json files in post processing queue
    for jsonFile, jsonRW in jsonRWs.iteritems():
      jsonRW.saveState()
      self.postProcessQueue.put(jsonFile)
    # Clean up by deleting levedb whose use is done 
    # since large files, might need to do it twice
    shutil.rmtree(leveldbFolder, ignore_errors=True)
    os.remove(prototxtWithNewLeveldb)
    time.sleep(5)
    shutil.rmtree(leveldbFolder, ignore_errors=True)
    time.sleep(5)
    # Finally, return success
    return True
