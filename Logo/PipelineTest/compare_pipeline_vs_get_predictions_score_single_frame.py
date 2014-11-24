#!/usr/bin/python

import sys, os, glob
import logging
import csv
from collections import OrderedDict

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.CSVReaderWriter import CSVReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'Usage %s <jsonFileName> <csvFileName>' % sys.argv[ 0 ]
		print '\n'
		print 'This executable will compare results from LogoPipeline and get_predictions.py.'
		print 'For each class in JSON, it will list the max, min and average score difference between'
		print 'the two methods.'
		print 'This script is intended to run after dump_patches_from_frame.py in PipelineTest.'
		print '\nPlease update Khajuri issue 50 to reflect changes to this file.'
		sys.exit(1)

	jsonFileName = sys.argv[1]
	csvFileName = sys.argv[2]

	jsonReaderWriter = JSONReaderWriter(jsonFileName)
	csvReaderWriter = CSVReaderWriter(csvFileName)
	classIds = csvReaderWriter.getClassIds()	

	# store differences
	diffMax = OrderedDict()
	diffMin = OrderedDict()
	diffAvg = OrderedDict()
	counter = 0
	for cls in classIds:
		diffMax[cls] = -1
		diffAvg[cls] = 0
		diffMin[cls] = 999

	print "patchFileName,class,jsonScore,csvScore"
	for scale in jsonReaderWriter.getScalingFactors():
		for patch in jsonReaderWriter.getPatches(scale):
			patchFileName = patch['patch_filename']
			for cls in classIds:
				jsonScore = patch['scores'][cls]
				csvScore = csvReaderWriter.getScoreForPatchFileNameClass(patchFileName, cls)
				diff = jsonScore - csvScore
				diffMax[cls] = max(diff, diffMax[cls])
				diffAvg[cls] = diff + diffAvg[cls]
				diffMin[cls] = min(diff, diffMin[cls])
				counter += 1
				print "%s, %s, %f, %f" % (patchFileName, cls, jsonScore, csvScore)

	print "\n\nclass,diffMax,diffAvg,diffMin"
	for cls in classIds:
		print "%s,%0.3f,%0.3f,%0.3f" % (cls, diffMax[cls], diffAvg[cls]/counter, diffMin[cls])
