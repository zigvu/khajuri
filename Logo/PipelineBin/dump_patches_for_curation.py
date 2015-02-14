#!/usr/bin/env python
import sys, os, time
import logging

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.CurationPatchDumper import CurationPatchDumper

if __name__ == "__main__":
  if len( sys.argv ) < 3:
    print 'Usage %s <config.yaml> <videoFileName>' % sys.argv[ 0 ]
    sys.exit( 1 )
  configFileName = sys.argv[ 1 ]
  videoFileName = sys.argv[ 2 ]

  configReader = ConfigReader(configFileName)
  jsonFolder = configReader.sw_folders_json
  outputFolder = configReader.sw_folders_patch
  # Logging levels
  logging.basicConfig(format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s', 
    level=configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

  curationPatchDumper = CurationPatchDumper(configReader, videoFileName, jsonFolder, outputFolder)
  curationPatchDumper.run()
