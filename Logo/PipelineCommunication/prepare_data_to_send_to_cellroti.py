#!/usr/bin/python

import sys, os, glob, time
import logging

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineCommunication.CellrotiDetectables import CellrotiDetectables
from Logo.PipelineCommunication.DetectableClassMapper import DetectableClassMapper
from Logo.PipelineCore.ConfigReader import ConfigReader

if __name__ == '__main__':
  if len(sys.argv) < 7:
    print 'Usage %s <config.yaml> <videoId> <videoFileName> <mappingFileName> <jsonFolder> <outputFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  startTime = time.time()

  configFileName = sys.argv[1]
  videoId = int(sys.argv[2])
  videoFileName = sys.argv[3]
  mappingFileName = sys.argv[4]
  jsonFolder = sys.argv[5]
  outputFolder = sys.argv[6]

  configReader = ConfigReader(configFileName)
  # Logging levels
  logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
    level=configReader.log_level)

  cellrotiDetectables = CellrotiDetectables()
  cellrotiDetectables.read_mapped_detectables(mappingFileName)

  detectableClassMapper = DetectableClassMapper(
    videoId, videoFileName, jsonFolder, outputFolder, cellrotiDetectables)
  detectableClassMapper.run()
  
  endTime = time.time()
  logging.info('It took %s %s seconds to complete' % ( sys.argv[0], endTime - startTime ))
