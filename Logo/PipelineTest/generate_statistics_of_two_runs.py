#!/usr/bin/python

import sys, os, glob
from collections import OrderedDict

from Logo.PipelineTest.JSONFolderStats import JSONFolderStats

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'Usage %s <jsonFolder1> <jsonFolder2>' % sys.argv[ 0 ]
		print '\n'
		print 'This executable will compare all JSON files in two folders and'
		print 'compute statistics of patch score differences across the two runs'
		sys.exit(1)

	jsonFolder1 = sys.argv[1]
	jsonFolder2 = sys.argv[2]

	jsonFolderStats = JSONFolderStats(jsonFolder1, jsonFolder2)

	print "\nScore difference standard deviation\n"
	jsonFolderStats.print_score_diff_std_dev()

	print "\nScore difference histogram\n"
	jsonFolderStats.print_score_diff_histogram(10)

	print "\nCorrelation between scores of two runs\n"
	jsonFolderStats.print_class_corrs()
