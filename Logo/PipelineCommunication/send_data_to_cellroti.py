#!/usr/bin/python

import sys, os, glob, time
import logging

from Logo.PipelineCommunication.CellrotiCommunication import CellrotiCommunication
from Logo.PipelineCommunication.DetectableClassMapper import DetectableClassMapper
from Logo.PipelineCore.ConfigReader import ConfigReader

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'Usage %s  <config.yaml> <extractedDataFolder>' % sys.argv[ 0 ]
		print '\n\nThis executable can be used to send extracted data to cellroti.'
		print 'All data is first saved to S3 bucket location (indexed by video_id) and a'
		print 'call is made to cellroti to inform the database of transfer of data.'
		print 'This needs to be done for each evaluated video.'
		print '\n<config.yaml> - Config file of Logo pipeline'
		print '<extractedDataFolder> - Folder in which to save files to send to cellroti or save to S3'
		sys.exit(1)

	configFileName = sys.argv[1]
	extractedDataFolder = sys.argv[2]


	configReader = ConfigReader(configFileName)
	httpurl = configReader.ce_urls_postResults
	storageSelection = configReader.ce_storageSelection
	storageLocation = configReader.ce_storageLocation

	# Logging levels
	logging.basicConfig(format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s', 
		level=configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

	startTime = time.time()

	cellrotiCommunication = CellrotiCommunication()

	logging.debug('Saving folder %s to %s' % (extractedDataFolder, storageLocation))
	saveState = cellrotiCommunication.send_data_to_cellroti(extractedDataFolder, storageSelection, storageLocation)
	if not saveState:
		raise RuntimeError("Couldn't save to specified location %s" % storageLocation)

	replyState = cellrotiCommunication.post_url(httpurl, saveState)
	if not ('success' in replyState.keys()):
		raise RuntimeError("Couldn't communicate with cellroti")

	logging.debug(replyState)

	endTime = time.time()
	logging.info('It took %s %s seconds to complete' % ( sys.argv[0], endTime - startTime ))
