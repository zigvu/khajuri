#!/usr/bin/python

import sys, os, glob, shutil
import logging
import csv, heapq, subprocess
from collections import OrderedDict

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.CSVReaderWriter import CSVReaderWriter
from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineMath.Rectangle import Rectangle

if __name__ == '__main__':
	if len(sys.argv) < 6:
		print 'Usage %s <jsonFolder> <videoFileName> <numPatchesPerClassToSave> <outputFolder> <test_patches.sh_executable>' % sys.argv[ 0 ]
		print '\n'
		print 'This executable will extract individial frames from videoFileName based on jsonFolder jsons,'
		print 'score them using get_predictions.py and save numPatchesPerClassToSave number of patches per class'
		print 'that have the highest score differences.'
		print '\nTo ensure that all executables are working, prior to running this script,'
		print 'it is recommended that you run'
		print '  * dump_patches_from_frame.py' 
		print '  * test_patches.sh'
		print '  * compare_pipleine_vs_get_predictions_single_frame.py'
		print '\n\nNOTE: You NEED to run this script from chia/CaffeSettings/logo directory'
		sys.exit(1)

	jsonFolder = sys.argv[1]
	videoFileName = sys.argv[2]
	numPatchesPerClassToSave = int(sys.argv[3])
	outputFolder = sys.argv[4]
	test_patches = sys.argv[5]

	tempfsFolder = '/mnt/tmp'
	frameFolder = os.path.join(tempfsFolder, "frames")
	ConfigReader.mkdir_p(frameFolder)
	patchFolder = os.path.join(tempfsFolder, "patches")
	ConfigReader.mkdir_p(patchFolder)
	resultFolder = os.path.join(outputFolder, "results")
	ConfigReader.rm_rf(resultFolder)
	ConfigReader.mkdir_p(resultFolder)

	patchWidth = 256
	patchHeight = 256
	videoFrameReader =  VideoFrameReader(videoFileName)

	# read all json files and organize based on frame number
	# we need frames in order
	frameIndex = {}
	jsonFiles = glob.glob(os.path.join(jsonFolder, "*json"))
	for jsonFileName in jsonFiles:
		jsonReaderWriter = JSONReaderWriter(jsonFileName)
		frameNumber = jsonReaderWriter.getFrameNumber()
		frameIndex[frameNumber] = jsonFileName
	totalNumOfFrames = len(frameIndex.keys())
	print "Total of " + str(totalNumOfFrames) + " frames"
	classIds = JSONReaderWriter(jsonFiles[0]).getClassIds()

	# for each class, create a new result folder
	for cls in classIds:
		clsRFolder = os.path.join(resultFolder, str(cls))
		ConfigReader.mkdir_p(clsRFolder)

	# for each class, create containers to store differences
	scoreHeaps = OrderedDict()
	for cls in classIds:
		scoreHeaps[cls] = []
		# put in numPatchesPerClassToSave items to seed
		for i in range(0, numPatchesPerClassToSave):
			# tuple format:
			# diffScore, pathFileName, jsonScore, csvScore
			heapq.heappush(scoreHeaps[cls], (-1, "NoFileYet", -1, -1))

	frameCounter = 0
	for frameNumber in sorted(frameIndex.keys()):
		print "Working on frame number %d (%d percent done)" % (frameNumber, (frameCounter * 100 / totalNumOfFrames))
		frameCounter += 1

		# delete old frames and patches
		for filename in glob.glob(os.path.join(frameFolder, "*")):
			os.remove(filename)
		for filename in glob.glob(os.path.join(patchFolder, "*")):
			os.remove(filename)

		# for each frame, extract patches in tempfs
		jsonReaderWriter = JSONReaderWriter(frameIndex[frameNumber])
		imageFileName = os.path.join(frameFolder, jsonReaderWriter.getFrameFileName())
		videoFrameReader.savePngWithFrameNumber(frameNumber, imageFileName)

		for scale in jsonReaderWriter.getScalingFactors():
			imageManipulator = ImageManipulator(imageFileName)
			imageManipulator.resize_image(scale)
			for patch in jsonReaderWriter.getPatches(scale):
				bbox = Rectangle.rectangle_from_json(patch['patch'])
				print "\t\tscale: %0.2f : %s" % (scale, bbox) 
				outputPatchName = os.path.join(patchFolder, patch['patch_filename'])
				imageManipulator.extract_patch(bbox, outputPatchName, patchWidth, patchHeight)
		
		# score using get_predictions.py
		print "\n\tRunning test_patches.sh"
		testPatchesCmd = "./%s %s" % (test_patches, patchFolder)
		p = subprocess.Popen(testPatchesCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		for line in p.stdout.readlines():
			print line,
		retval = p.wait()
		print "%d" % retval
	
		# for each class, compare score differences between pipeline method and get_predictions
		#csvFileName = '/home/evan/Vision/temp/test_leveldb/csv_json_compare/CSV/patches-frame_1.csv'
		csvFileName = os.path.join(tempfsFolder, "patches.csv")
		csvReaderWriter = CSVReaderWriter(csvFileName)

		# evaluate score differences
		for scale in jsonReaderWriter.getScalingFactors():
			for patch in jsonReaderWriter.getPatches(scale):
				patchFileName = patch['patch_filename']
				for cls in classIds:
					jsonScore = patch['scores'][cls]
					csvScore = csvReaderWriter.getScoreForPatchFileNameClass(patchFileName, cls)
					diffScore = abs(jsonScore - csvScore)
					# tuple format:
					# diffScore, patchFileName, jsonScore, csvScore
					newItem = (diffScore, patchFileName, jsonScore, csvScore)
					itemRemoved = heapq.heappushpop(scoreHeaps[cls], newItem)
					# if the pushed item is new, delete old patch and put in new one
					if newItem[1] != itemRemoved[1]:
						try:
							os.remove(os.path.join(resultFolder, str(cls), itemRemoved[1]))
						except:
							pass
						shutil.copy(os.path.join(patchFolder, patchFileName), os.path.join(resultFolder, str(cls)))
		# end evaluate score differences
		break
	# end json file iterations

	# print results and rename files
	print "Class,ScoreDiff,PatchFileName,JSONScore,CSVScore"
	for cls in classIds:
		for i in range(0, numPatchesPerClassToSave):
			ir = heapq.heappop(scoreHeaps[cls])
			oldName = os.path.join(resultFolder, str(cls), ir[1])
			newName = os.path.join(resultFolder, str(cls), "%0.2f_%s" % (ir[0], ir[1]))
			os.rename(oldName, newName)
			print "%s,%.4f,%s,%.4f,%.4f" % (cls, ir[0], ir[1], ir[2], ir[3])

	print "Waiting for videoFrameReader to close"
	videoFrameReader.close()
