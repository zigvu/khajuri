#!/usr/bin/python

import sys, os, glob

from Logo.PipelineTest.JSONFileComparer import JSONFileComparer

if __name__ == '__main__':
	if len(sys.argv) < 4:
		print 'Usage %s <jsonFileName1> <jsonFileName2> <compareLocCuration>' % sys.argv[ 0 ]
		print '\n'
		print 'if <compareLocCuration> is 1, compare both localizations and curations'
		print 'if <compareLocCuration> is 0, do NOT compare either localizations and curations'
		print 'This executable will compare two JSON files and print any differences per class'
		sys.exit(1)

	jsonFileName1 = sys.argv[1]
	jsonFileName2 = sys.argv[2]
	compareLocCuration = int(sys.argv[3])

	jsonFileComparer = JSONFileComparer(jsonFileName1, jsonFileName2)
	diffMax, diffAvg, diffMin = jsonFileComparer.get_diff_patch_scores(True)

	if compareLocCuration == 1:
		diffNumBboxesLoc, diffXPosOfBboxesLoc, diffYPosOfBboxesLoc, diffAreaOfBboxesLoc, diffScoreOfBboxesLoc = \
			jsonFileComparer.get_diff_post_processing("localization", True)

		diffNumBboxesCur, diffXPosOfBboxesCur, diffYPosOfBboxesCur, diffAreaOfBboxesCur, diffScoreOfBboxesCur = \
			jsonFileComparer.get_diff_post_processing("curation", True)

	print "\n\nSummary: Patch score differences"
	print "class,diffMax,diffAvg,diffMin"
	for cls in jsonFileComparer.get_class_ids():
		print "%s,%0.3f,%0.3f,%0.3f" % (cls, diffMax[cls], diffAvg[cls], diffMin[cls])

	if compareLocCuration == 1:
		print "\n\nSummary: Localization score differences"
		print "class,diffNumBboxes,diffXPosOfBboxes,diffYPosOfBboxes,diffAreaOfBboxes,diffScoreOfBboxes"
		for cls in jsonFileComparer.get_class_ids():
			print "%s,%d,%d,%d,%d,%0.3f" % (cls, 
				diffNumBboxesLoc[cls], diffXPosOfBboxesLoc[cls], 
				diffYPosOfBboxesLoc[cls], diffAreaOfBboxesLoc[cls], diffScoreOfBboxesLoc[cls])

		print "\n\nSummary: Curation score differences"
		print "class,diffNumBboxes,diffXPosOfBboxes,diffYPosOfBboxes,diffAreaOfBboxes,diffScoreOfBboxes"
		for cls in jsonFileComparer.get_class_ids():
			print "%s,%d,%d,%d,%d,%0.3f" % (cls, 
				diffNumBboxesCur[cls], diffXPosOfBboxesCur[cls], 
				diffYPosOfBboxesCur[cls], diffAreaOfBboxesCur[cls], diffScoreOfBboxesCur[cls])

