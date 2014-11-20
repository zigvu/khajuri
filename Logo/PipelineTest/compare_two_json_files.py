#!/usr/bin/python

import sys, os, glob
import logging
from collections import OrderedDict

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'Usage %s <jsonFileName1> <jsonFileName2>' % sys.argv[ 0 ]
		print '\n'
		print 'This executable will compare two JSON files and print any differences per class'
		sys.exit(1)

	jsonFileName1 = sys.argv[1]
	jsonFileName2 = sys.argv[2]

	jrw1 = JSONReaderWriter(jsonFileName1)
	jrw2 = JSONReaderWriter(jsonFileName2)

	# store differences
	diffMax = OrderedDict()
	diffMin = OrderedDict()
	diffAvg = OrderedDict()
	counter = 0
	for cls in jrw1.getClassIds():
		diffMax[cls] = -1
		diffAvg[cls] = 0
		diffMin[cls] = 999

	# loop through all scales and dump sliding window patches at each scale
	print "patchFileName,class,jsonScore1,jsonScore2"
	for scale in jrw1.getScalingFactors():
		for patch1 in jrw1.getPatches(scale):
			patchFileName = patch1['patch_filename']

			# for second json
			for patch2 in jrw2.getPatches(scale):
				if patchFileName == patch2['patch_filename']:
					# compare scores
					for cls in jrw1.getClassIds():
						jsonScore1 = patch1['scores'][cls]
						jsonScore2 = patch2['scores'][cls]
						diff = jsonScore1 - jsonScore2
						diffMax[cls] = max(diff, diffMax[cls])
						diffAvg[cls] = diff + diffAvg[cls]
						diffMin[cls] = min(diff, diffMin[cls])
						counter += 1
						print "%s, %s, %f, %f" % (patchFileName, cls, jsonScore1, jsonScore2)

	print "\n\nclass,diffMax,diffAvg,diffMin"
	for cls in jrw1.getClassIds():
		print "%s,%0.3f,%0.3f,%0.3f" % (cls, diffMax[cls], diffAvg[cls]/counter, diffMin[cls])
