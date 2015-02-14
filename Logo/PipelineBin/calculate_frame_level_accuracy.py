#!/usr/bin/python

import os, sys, re, time
import json, math
from collections import OrderedDict
import logging

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.CurationManager import CurationManager

def getFrameNumbers(fileWithFrameNames):
  """Get frame numbers from file"""
  # Read file with frame names and extract frame numbers
  frameNumbers = []
  with open(fileWithFrameNames) as fread:
    for line in fread:
      frameNumbers += [int(line.strip(" \n").split("_frame_")[1].split(".")[0])]
  return frameNumbers

if __name__ == '__main__':
  if len(sys.argv) < 5:
    print 'Usage %s <config.yaml> <classId> <classFrameNames> <backgroundFrameNames>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  classId = str(sys.argv[2])
  classFrameNames = sys.argv[3]
  backgroundFrameNames = sys.argv[4]
  
  configReader = ConfigReader(configFileName)
  jsonFolder = configReader.sw_folders_json
  # Logging levels
  logging.basicConfig(format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s', 
    level=configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

  classFrameNumbers = getFrameNumbers(classFrameNames)
  backgroundFrameNumbers = getFrameNumbers(backgroundFrameNames)

  # initialize counters
  tp_clean = 0; fp_clean = 0; tn_clean = 0; fn_clean = 0;
  tp_border = 0; fp_border = 0; tn_border = 0; fn_border = 0;

  curationManager = CurationManager(jsonFolder, configReader)
  for frameNumber in curationManager.getFrameNumbers():
    detectionCount = curationManager.getDetectionCount(frameNumber, classId)
    logging.debug("Frame: %d, DetectionCount: %d" % (frameNumber, detectionCount))
    if frameNumber in classFrameNumbers:
      if detectionCount > 0:
        tp_border += 1
        if not frameNumber in backgroundFrameNumbers:
          tp_clean += 1
      else:
        fn_border += 1
        if not frameNumber in backgroundFrameNumbers:
          fn_clean += 1
    else:
      if detectionCount > 0:
        fp_clean += 1
        fp_border += 1
      else:
        tn_clean += 1
        tn_border += 1

  print "Clean: TP,FP,TN,FN"
  print "%d,%d,%d,%d" % (tp_clean, fp_clean, tn_clean, fn_clean)

  print "Border: TP,FP,TN,FN"
  print "%d,%d,%d,%d" % (tp_border, fp_border, tn_border, fn_border)
