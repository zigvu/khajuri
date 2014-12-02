#!/usr/bin/python

import sys, os, glob
from collections import OrderedDict

from Logo.PipelineTest.JSONFileComparer import JSONFileComparer

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'Usage %s <jsonFolder1> <jsonFolder2>' % sys.argv[ 0 ]
		print '\n'
		print 'This executable will compare all JSON files in two folders and'
		print 'print differences between classes across all files. Assumes that files are same'
		print 'in both the folders'
		sys.exit(1)

	jsonFolder1 = sys.argv[1]
	jsonFolder2 = sys.argv[2]

	jsonFolder1Files = glob.glob("%s/*.json" % jsonFolder1)
	jsonFolder2Files = glob.glob("%s/*.json" % jsonFolder2)

	jsonFileComparer = JSONFileComparer(jsonFolder1Files[0], jsonFolder2Files[0])
	classes = jsonFileComparer.get_class_ids()

	adiffMax = OrderedDict()
	adiffAvg = OrderedDict()
	adiffMin = OrderedDict()
	for cls in classes:
		adiffMax[cls] = {'value': -1, 'filename': None}
		adiffAvg[cls] = {'value': 0, 'filename': None}
		adiffMin[cls] = {'value': 999, 'filename': None}

	for f in jsonFolder1Files:
		jsonFile = os.path.basename(f)
		jsonFileName1 = os.path.join(jsonFolder1, jsonFile)
		jsonFileName2 = os.path.join(jsonFolder2, jsonFile)
		jsonFileComparer = JSONFileComparer(jsonFileName1, jsonFileName2)
		diffMax, diffAvg, diffMin = jsonFileComparer.get_diff_patch_scores()

		# store results:
		for cls in classes:
			if diffMax[cls] > adiffMax[cls]['value']:
				adiffMax[cls]['value'] = diffMax[cls]
				adiffMax[cls]['filename'] = jsonFile
			
			if diffAvg[cls] > adiffAvg[cls]['value']:
				adiffAvg[cls]['value'] = diffAvg[cls]
				adiffAvg[cls]['filename'] = jsonFile
			
			if diffMin[cls] < adiffMin[cls]['value']:
				adiffMin[cls]['value'] = diffMin[cls]
				adiffMin[cls]['filename'] = jsonFile

	print "\n\nMax\nclass,diffMax,diffAvg,diffMin"
	for cls in classes:
		print "%s,%0.3f,%s" % (cls, adiffMax[cls]['value'], adiffMax[cls]['filename'])

	print "\n\nAvg\nclass,diffMax,diffAvg,diffMin"
	for cls in classes:
		print "%s,%0.3f,%s" % (cls, adiffAvg[cls]['value'], adiffAvg[cls]['filename'])

	print "\n\nMin\nclass,diffMax,diffAvg,diffMin"
	for cls in classes:
		print "%s,%0.3f,%s" % (cls, adiffMin[cls]['value'], adiffMin[cls]['filename'])
