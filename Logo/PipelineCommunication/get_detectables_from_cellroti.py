#!/usr/bin/python

import sys, os, glob, time
import logging

from Logo.PipelineCommunication.CellrotiDetectables import CellrotiDetectables
from Logo.PipelineCore.ConfigReader import ConfigReader

if __name__ == '__main__':
	if len(sys.argv) < 4:
		print 'Usage %s  <config.yaml> <outputFileName> <httpurl>' % sys.argv[ 0 ]
		sys.exit(1)

	configFileName = sys.argv[1]
	outputFileName = sys.argv[2]
	httpurl = sys.argv[3]


	configReader = ConfigReader(configFileName)
	# Logging levels
  logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
    level=configReader.log_level)

	startTime = time.time()
	cellrotiDetectables = CellrotiDetectables()
	cellrotiDetectables.download_detectables(outputFileName, httpurl)
	endTime = time.time()

	logging.info('It took %s %s seconds to complete' % ( sys.argv[0], endTime - startTime ))