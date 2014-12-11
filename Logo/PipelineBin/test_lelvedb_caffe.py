#!/usr/bin/python

import os, sys, re, time
import json, math
from collections import OrderedDict
import logging

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

import caffe
import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter

if __name__ == '__main__':
  if len(sys.argv) < 5:
    print 'Usage %s <config.yaml> <videoFileName> <extractFrameNumber> <outputFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  extractFrameNumber = int(sys.argv[3])
  outputFolder = sys.argv[4]

  configReader = ConfigReader(configFileName)
  videoId = os.path.basename(videoFileName).split('.')[0]
  patchFolder = os.path.join(outputFolder, configReader.sw_folders_patch)
  ConfigReader.mkdir_p(outputFolder)
  ConfigReader.mkdir_p(patchFolder)

  prototxtFile = configReader.ci_video_prototxtFile
  modelFile = configReader.ci_modelFile

  # Logging levels
  logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
    level=configReader.log_level)

  # Load video - since no expilicit synchronization exists to check if
  # VideoReader is ready, wait for 10 seconds
  videoFrameReader = VideoReader.VideoFrameReader(40, 40, videoFileName)
  videoFrameReader.generateFrames()
  time.sleep(1)

  # Get frame dimensions and create bounding boxes
  frame = videoFrameReader.getFrameWithFrameNumber(1)
  while not frame:
    frame = videoFrameReader.getFrameWithFrameNumber(1)
  imageDim = Rectangle.rectangle_from_dimensions(frame.width, frame.height)
  patchDimension = Rectangle.rectangle_from_dimensions(\
    configReader.sw_patchWidth, configReader.sw_patchHeight)
  staticBoundingBoxes = BoundingBoxes(imageDim, \
    configReader.sw_xStride, configReader.sw_xStride, patchDimension)

  curLeveldbFolder = os.path.join(outputFolder, "%s_leveldb_%d" % (videoId, 0))
  leveldbMappingFile = os.path.join(curLeveldbFolder, "leveldb_mapping.json")
  videoDb = VideoReader.VideoDb(curLeveldbFolder)
  videoDb.setVideoFrameReader(videoFrameReader)
  leveldbMapping = OrderedDict()

  # Main loop to go through video
  currentFrameNum = configReader.ci_videoFrameNumberStart
  jsonAnnotation = None
  logging.info("Start patch extraction")
  while (not videoFrameReader.eof) or (currentFrameNum <= videoFrameReader.totalFrames):
    frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
    while not frame:
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
    if currentFrameNum == extractFrameNumber:
      logging.debug("Extracting frame %d" % currentFrameNum)
      # Start json annotation file
      jsonFileName = os.path.join(outputFolder, "%s_frame_%s.json" % (videoId, currentFrameNum))
      jsonAnnotation = JSONReaderWriter(jsonFileName, create_new=True)
      jsonAnnotation.initializeJSON(videoId, currentFrameNum, imageDim, configReader.sw_scales)
      frameFileName = os.path.join(outputFolder, jsonAnnotation.getFrameFileName())
      videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), frameFileName)
      # Put patch into leveldb
      for scale in configReader.sw_scales:
        patchNum = 0
        for box in staticBoundingBoxes.getBoundingBoxes(scale):
          patchFileName = '%s_frame_%s_scl_%s_idx_%s.png' % (\
            videoId, currentFrameNum, scale, patchNum)
          # Generate leveldb patch and add to json
          leveldbPatchCounter = videoDb.savePatch(currentFrameNum, scale, \
            box[0], box[1], box[2], box[3])
          videoFrameReader.patchFromFrameNumber(int(currentFrameNum), \
            os.path.join(patchFolder, patchFileName), scale, \
            box[0], box[1], box[2], box [3])
          jsonAnnotation.addPatch(scale, patchNum, leveldbPatchCounter, \
            box[0], box[1], box[2], box [3])
          leveldbMapping[leveldbPatchCounter] = patchFileName
          # Increment counters
          patchNum += 1
      # Save annotation file
      jsonAnnotation.saveState()
    else:
      logging.debug("Skipping frame %d" % currentFrameNum)
    if currentFrameNum > extractFrameNumber:
      break
    currentFrameNum += configReader.sw_frame_density

  videoDb.saveLevelDb()
  with open(leveldbMappingFile, "w") as f :
    json.dump(leveldbMapping, f, indent=2)

  if jsonAnnotation is None:
    raise RuntimeError("Frame and associated JSON file NOT saved")

  caffeBatchSize = -1
  # Create new prototxt file to point to right leveldb
  prototxtWithNewLeveldb = os.path.join(os.path.dirname(curLeveldbFolder), \
    'prototxt_%s.prototxt' % os.path.basename(curLeveldbFolder))
  with open(prototxtFile) as fread:
    lines = fread.readlines()
  with open(prototxtWithNewLeveldb, "w") as fwrite:
    for line in lines:
      if "source:" in line:
        line = line.replace(re.findall(r'\"(.+?)\"', line)[0], curLeveldbFolder)
      if "batch_size:" in line:
        caffeBatchSize = int(line.strip(" \n").split("batch_size: ")[1])
      fwrite.write("%s" % line)

  # Read mapping
  maxPatchCounter = 0
  for patchCounter, jsonFile in leveldbMapping.iteritems():
    if maxPatchCounter < int(patchCounter):
      maxPatchCounter = int(patchCounter)

  # HACK: without reinitializing caffe_net twice, it won't give reproducible results
  # Seems to happen in both CPU and GPU runs:
  logging.debug("Initializing caffe_net")
  caffe_net = caffe.Net(prototxtWithNewLeveldb, modelFile)
  caffe_net.set_phase_test() 
  if configReader.ci_useGPU:
    caffe_net.set_mode_gpu()
  else:
    caffe_net.set_mode_cpu()
  logging.debug("Reinitializing caffe_net")

  # Run caffe net
  # counter for iteration starts at 0, so increment 1 to maxPatchCounter
  numOutputIteration = int(math.ceil((maxPatchCounter + 1) * 1.0 / caffeBatchSize))
  numOfClasses = len(configReader.ci_allClassIds)
  caffe_net = caffe.Net(prototxtWithNewLeveldb, modelFile)
  caffe_net.set_phase_test()
  if configReader.ci_useGPU:
    caffe_net.set_mode_gpu()
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
        scores[configReader.ci_allClassIds[j]] = probablities[k][j].item(0)
        printStr = "%s,%f" % (printStr, scores[configReader.ci_allClassIds[j]])
      # Note: if number of patches is not multiple of batch size, then caffe
      #  displays results for patches in the begining of leveldb
      if patchCounter <= maxPatchCounter:
        curPatchNumber = int(output['label'].item(k))
        printStr = "%s%s" % (leveldbMapping[curPatchNumber] , printStr)
        jsonAnnotation.addScores(curPatchNumber, scores)
        print printStr
      patchCounter += 1

  # Save annotation file
  jsonAnnotation.saveState()
  # Save file to CSV as well
  csvFileName = os.path.join(outputFolder, "%s_frame_%s.csv" % (videoId, \
    str(jsonAnnotation.getFrameNumber())))
  jsonAnnotation.saveToCSV(csvFileName)
  
  # HACK: work around so that videoDb releases lock on curLeveldbFolder
  videoDb = None
  # HACK: quit video reader gracefully
  logging.debug("Getting to end of video reader")
  currentFrameNum = videoFrameReader.totalFrames
  while not videoFrameReader.eof or currentFrameNum <= videoFrameReader.totalFrames:
    videoFrameReader.seekToFrameWithFrameNumber(currentFrameNum)
    currentFrameNum += 1
