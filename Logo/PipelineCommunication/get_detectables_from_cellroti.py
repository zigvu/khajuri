#!/usr/bin/python

import sys, os, glob, time
import logging

from Logo.PipelineCommunication.CellrotiCommunication import CellrotiCommunication
from Logo.PipelineCommunication.DetectableClassMapper import DetectableClassMapper
from Logo.PipelineCore.ConfigReader import ConfigReader

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'Usage %s  <config.yaml> <outputFileName>' % sys.argv[ 0 ]
		print '\n\nThis executable can be used to get the list of detectables from cellroti.'
		print 'This script needs to be run once for each chia model. After running this script'
		print 'change the outputFileName to match the chia class label mapping with cellroti'
		print 'detectable id matching. Once that is done, you can run prepare_data_to_send_to_cellroti'
		print '\nAssumes that cellroti admin username/authtokens are in environment variables'
		sys.exit(1)

	configFileName = sys.argv[1]
	outputFileName = sys.argv[2]

	configReader = ConfigReader(configFileName)
	httpurl = configReader.ce_urls_getDetectables
	# Logging levels
	logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
		level=configReader.log_level)

	startTime = time.time()
	cellrotiCommunication = CellrotiCommunication()
	detectableList = cellrotiCommunication.get_url(httpurl)
	
	detectableClassMapper = DetectableClassMapper()
	detectableClassMapper.save_detectable_list(outputFileName, detectableList)

	endTime = time.time()
	logging.info('It took %s %s seconds to complete' % ( sys.argv[0], endTime - startTime ))
	