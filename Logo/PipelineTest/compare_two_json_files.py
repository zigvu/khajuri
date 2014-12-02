#!/usr/bin/python

import sys, os, glob

from Logo.PipelineTest.JSONFileComparer import JSONFileComparer

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'Usage %s <jsonFileName1> <jsonFileName2>' % sys.argv[ 0 ]
		print '\n'
		print 'This executable will compare two JSON files and print any differences per class'
		sys.exit(1)

	jsonFileName1 = sys.argv[1]
	jsonFileName2 = sys.argv[2]

	jsonFileComparer = JSONFileComparer(jsonFileName1, jsonFileName2)
	diffMax, diffAvg, diffMin = jsonFileComparer.get_diff_patch_scores(True)

	print "\n\nclass,diffMax,diffAvg,diffMin"
	for cls in jsonFileComparer.get_class_ids():
		print "%s,%0.3f,%0.3f,%0.3f" % (cls, diffMax[cls], diffAvg[cls], diffMin[cls])
