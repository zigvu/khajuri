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
		sys.exit(1)

	configFileName = sys.argv[1]
	extractedDataFolder = sys.argv[2]


	configReader = ConfigReader(configFileName)
	httpurl = configReader.ce_urls_postResults
	s3BucketVideos = configReader.ce_s3bucket_videos
	# Logging levels
	logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
		level=configReader.log_level)

	startTime = time.time()

	cellrotiCommunication = CellrotiCommunication()

	# save to S3
	saveState = {'video_id': 1, 'success': True}
	

	# successState = cellrotiCommunication.post_url(httpurl, saveState)
	# print successState


	endTime = time.time()
	logging.info('It took %s %s seconds to complete' % ( sys.argv[0], endTime - startTime ))
