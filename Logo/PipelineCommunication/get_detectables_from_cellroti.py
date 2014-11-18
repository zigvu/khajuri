#!/usr/bin/python

import sys, os, glob, time

from Logo.PipelineCommunication.CellrotiDetectables import CellrotiDetectables

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'Usage %s <outputFileName> <httpurl>' % sys.argv[ 0 ]
		sys.exit(1)

	outputFileName = sys.argv[1]
	httpurl = sys.argv[2]

	cellrotiDetectables = CellrotiDetectables()
	cellrotiDetectables.download_detectables(outputFileName, httpurl)
