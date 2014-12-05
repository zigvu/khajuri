#!/usr/bin/python

import sys, os, glob
import logging

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineMath.Rectangle import Rectangle

if __name__ == '__main__':
	if len(sys.argv) < 4:
		print 'Usage %s <frameFileName> <jsonFileName> <outputFolder>' % sys.argv[ 0 ]
		print '\n'
		print 'This executable will dump all sliding windows present in the jsonFileName at each scale.'
		print 'To keep track of patches, patchnames are extracted from jsonFileName.'
		print '\nPlease update Khajuri issue 50 to reflect changes to this file.'
		sys.exit(1)

	frameFileName = sys.argv[1]
	jsonFileName = sys.argv[2]
	outputFolder = sys.argv[3]

	patchWidth = 256
	patchHeight = 256

	ConfigReader.mkdir_p(outputFolder)

	imageManipulator = ImageManipulator(frameFileName)

	# loop through all scales and dump sliding window patches at each scale
	jsonAnnotation = JSONReaderWriter(jsonFileName)
	for scale in jsonAnnotation.getScalingFactors():
		imageManipulator = ImageManipulator(frameFileName)
		imageManipulator.resize_image(scale)
		for patch in jsonAnnotation.getPatches(scale):
			bbox = Rectangle.rectangle_from_json(patch['patch'])
			print "scale: %0.2f : %s" % (scale, bbox) 
			outputPatchName = os.path.join(outputFolder, patch['patch_filename'])
			imageManipulator.extract_patch(bbox, outputPatchName, patchWidth, patchHeight)
