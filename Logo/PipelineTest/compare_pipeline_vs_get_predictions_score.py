#!/usr/bin/python

import sys, os, glob
import logging
import csv
from collections import OrderedDict

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
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

	# read CSV file and construct dictionary
	csvClassIdx = {}
	csvData = OrderedDict()
	patchFileName = None
	with open(csvFileName, 'rb') as f:
		reader = csv.reader(f)
		for idx, row in enumerate(reader):
			for i, rowItem in enumerate(row):
				# get indices of class from header
				if idx == 0:
					if i == 0:
						pass
					else:
						csvClassIdx[i] = rowItem.split("_")[1]
				# once we have header, get individual class scores
				else:
					if i == 0:
						patchFileName = rowItem
						csvData[patchFileName] = OrderedDict()
					else:
						csvData[patchFileName][csvClassIdx[i]] = rowItem

	# store differences
	diffMax = OrderedDict()
	diffMin = OrderedDict()
	diffAvg = OrderedDict()
	counter = 0
	for i in csvClassIdx:
		diffMax[csvClassIdx[i]] = -1
		diffAvg[csvClassIdx[i]] = 0
		diffMin[csvClassIdx[i]] = 999

	# loop through all scales and dump sliding window patches at each scale
	jsonAnnotation = JSONReaderWriter(jsonFileName)
	print "patchFileName,class,jsonScore,csvScore"
	for scale in jsonAnnotation.getScalingFactors():
		for patch in jsonAnnotation.getPatches(scale):
			patchFileName = patch['patch_filename']
			for i in csvClassIdx:
				cls = csvClassIdx[i]
				jsonScore = patch['scores'][cls]
				csvScore = float(csvData[patchFileName][cls])
				diff = jsonScore - csvScore
				diffMax[cls] = max(diff, diffMax[cls])
				diffAvg[cls] = diff + diffAvg[cls]
				diffMin[cls] = min(diff, diffMin[cls])
				counter += 1
				print "%s, %s, %f, %f" % (patchFileName, cls, jsonScore, csvScore)

	print "\n\nclass,diffMax,diffAvg,diffMin"
	for i in csvClassIdx:
		cls = csvClassIdx[i]
		print "%s,%0.3f,%0.3f,%0.3f" % (cls, diffMax[cls], diffAvg[cls]/counter, diffMin[cls])
