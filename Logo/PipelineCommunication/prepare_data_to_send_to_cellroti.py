#!/usr/bin/python

import sys, os, glob, time
import logging

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineCommunication.DetectableClassMapper import DetectableClassMapper
from Logo.PipelineCommunication.PostProcessDataExtractor import PostProcessDataExtractor
from Logo.PipelineCore.ConfigReader import ConfigReader

if __name__ == '__main__':
  if len(sys.argv) < 7:
    print 'Usage %s <config.yaml> <videoId> <videoFileName> <mappingFileName> <jsonFolder> <outputFolder>' % sys.argv[ 0 ]
    print '\n\nThis executable can be used to prepare post-processed data to send to cellroti.'
    print 'This needs to be run for each evaluated video prior to sending the data to cellroti.'
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

  detectableClassMapper = DetectableClassMapper()
  detectableClassMapper.read_mapped_detectables(mappingFileName)

  postProcessDataExtractor = PostProcessDataExtractor(
    videoId, videoFileName, jsonFolder, outputFolder, cellrotiDetectables)
  postProcessDataExtractor.run()
  
  endTime = time.time()
  logging.info('It took %s %s seconds to complete' % ( sys.argv[0], endTime - startTime ))
