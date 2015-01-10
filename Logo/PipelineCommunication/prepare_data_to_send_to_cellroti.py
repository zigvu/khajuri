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
    print 'Usage %s <config.yaml> <videoId> <videoFileName> <mappingFileName> <jsonFolder> <extractedDataFolder>' % sys.argv[ 0 ]
    print '\n\nThis executable can be used to prepare post-processed data to send to cellroti.'
    print 'This needs to be run for each evaluated video prior to sending the data to cellroti.'
    print '\n<config.yaml> - Config file of Logo pipeline'
    print '<videoId> - ID of video in cellroti database'
    print '<videoFileName> - Path of video in local system'
    print '<mappingFileName> - File that has both chia class labels and cellroti detectable ids'
    print '<jsonFolder> - Output of running post-processing on video'
    print '<extractedDataFolder> - Folder in which to save files to send to cellroti or save to S3'
    sys.exit(1)

  startTime = time.time()

  configFileName = sys.argv[1]
  videoId = int(sys.argv[2])
  videoFileName = sys.argv[3]
  mappingFileName = sys.argv[4]
  jsonFolder = sys.argv[5]
  extractedDataFolder = sys.argv[6]

  configReader = ConfigReader(configFileName)
  # Logging levels
  logging.basicConfig(format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s', 
    level=configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

  detectableClassMapper = DetectableClassMapper()
  detectableClassMapper.read_mapped_detectables(mappingFileName)

  postProcessDataExtractor = PostProcessDataExtractor(
    configReader, videoId, videoFileName, jsonFolder, extractedDataFolder, detectableClassMapper)
  postProcessDataExtractor.run()
  
  endTime = time.time()
  logging.info('It took %s %s seconds to complete' % ( sys.argv[0], endTime - startTime ))
