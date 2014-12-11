#!/usr/bin/python

import sys, os, glob
from collections import OrderedDict

from Logo.PipelineTest.JSONFileComparer import JSONFileComparer

if __name__ == '__main__':
	if len(sys.argv) < 4:
		print 'Usage %s <jsonFolder1> <jsonFolder2> <compareLocCuration>' % sys.argv[ 0 ]
		print '\n'
		print 'if <compareLocCuration> is 1, compare both localizations and curations'
		print 'if <compareLocCuration> is 0, do NOT compare either localizations and curations'
		print '\n'
		print 'This executable will compare all JSON files in two folders and'
		print 'print differences between classes across all files. Assumes that files are same'
		print 'in both the folders'
		sys.exit(1)

	jsonFolder1 = sys.argv[1]
	jsonFolder2 = sys.argv[2]
	compareLocCuration = int(sys.argv[3])

	jsonFolder1Files = glob.glob("%s/*.json" % jsonFolder1)
	jsonFolder2Files = glob.glob("%s/*.json" % jsonFolder2)

	jsonFileComparer = JSONFileComparer(jsonFolder1Files[0], jsonFolder2Files[0])
	classes = jsonFileComparer.get_class_ids()

	adiffMax = OrderedDict()
	adiffAvg = OrderedDict()
	adiffMin = OrderedDict()

	aDiffNumBboxesLoc = OrderedDict()
	aDiffScoreOfBboxesLoc = OrderedDict()
	aDiffNumBboxesCur = OrderedDict()
	aDiffScoreOfBboxesCur = OrderedDict()

	for cls in classes:
		adiffMax[cls] = {'value': -1, 'filename': None}
		adiffAvg[cls] = {'value': 0, 'filename': None}
		adiffMin[cls] = {'value': 999, 'filename': None}

		aDiffNumBboxesLoc[cls] = {'value': 0, 'filename': None}
		aDiffScoreOfBboxesLoc[cls] = {'value': -1, 'filename': None}
		aDiffNumBboxesCur[cls] = {'value': 0, 'filename': None}
		aDiffScoreOfBboxesCur[cls] = {'value': -1, 'filename': None}

	for f in jsonFolder1Files:
		jsonFile = os.path.basename(f)
		jsonFileName1 = os.path.join(jsonFolder1, jsonFile)
		jsonFileName2 = os.path.join(jsonFolder2, jsonFile)
		jsonFileComparer = JSONFileComparer(jsonFileName1, jsonFileName2)
		diffMax, diffAvg, diffMin = jsonFileComparer.get_diff_patch_scores()
		if compareLocCuration == 1:
			diffNumBboxesLoc, diffXPosOfBboxesLoc, diffYPosOfBboxesLoc, diffAreaOfBboxesLoc, diffScoreOfBboxesLoc = \
				jsonFileComparer.get_diff_post_processing("localization")
			diffNumBboxesCur, diffXPosOfBboxesCur, diffYPosOfBboxesCur, diffAreaOfBboxesCur, diffScoreOfBboxesCur = \
				jsonFileComparer.get_diff_post_processing("curation")

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

			if compareLocCuration == 1:
				if diffNumBboxesLoc[cls] > aDiffNumBboxesLoc[cls]['value']:
					aDiffNumBboxesLoc[cls]['value'] = diffNumBboxesLoc[cls]
					aDiffNumBboxesLoc[cls]['filename'] = jsonFile

				if diffScoreOfBboxesLoc[cls] > aDiffScoreOfBboxesLoc[cls]['value']:
					aDiffScoreOfBboxesLoc[cls]['value'] = diffScoreOfBboxesLoc[cls]
					aDiffScoreOfBboxesLoc[cls]['filename'] = jsonFile

				if diffNumBboxesCur[cls] > aDiffNumBboxesCur[cls]['value']:
					aDiffNumBboxesCur[cls]['value'] = diffNumBboxesCur[cls]
					aDiffNumBboxesCur[cls]['filename'] = jsonFile

				if diffScoreOfBboxesCur[cls] > aDiffScoreOfBboxesCur[cls]['value']:
					aDiffScoreOfBboxesCur[cls]['value'] = diffScoreOfBboxesCur[cls]
					aDiffScoreOfBboxesCur[cls]['filename'] = jsonFile


	print "\n\nPatch Score Max\nclass,score,filename"
	for cls in classes:
		print "%s,%0.3f,%s" % (cls, adiffMax[cls]['value'], adiffMax[cls]['filename'])

	print "\n\nPatch Score Avg\nclass,score,filename"
	for cls in classes:
		print "%s,%0.3f,%s" % (cls, adiffAvg[cls]['value'], adiffAvg[cls]['filename'])

	print "\n\nPatch Score Min\nclass,score,filename"
	for cls in classes:
		print "%s,%0.3f,%s" % (cls, adiffMin[cls]['value'], adiffMin[cls]['filename'])

	if compareLocCuration == 1:
		print "\n\nLocalization Num Bbox Diff\nclass,score,filename"
		for cls in classes:
			print "%s,%0.3f,%s" % (cls, aDiffNumBboxesLoc[cls]['value'], aDiffNumBboxesLoc[cls]['filename'])

		print "\n\nLocalization Score Diff\nclass,score,filename"
		for cls in classes:
			print "%s,%0.3f,%s" % (cls, aDiffScoreOfBboxesLoc[cls]['value'], aDiffScoreOfBboxesLoc[cls]['filename'])

		print "\n\nCuration Num Bbox Diff\nclass,score,filename"
		for cls in classes:
			print "%s,%0.3f,%s" % (cls, aDiffNumBboxesCur[cls]['value'], aDiffNumBboxesCur[cls]['filename'])

		print "\n\nCuration Score Diff\nclass,score,filename"
		for cls in classes:
			print "%s,%0.3f,%s" % (cls, aDiffScoreOfBboxesCur[cls]['value'], aDiffScoreOfBboxesCur[cls]['filename'])
