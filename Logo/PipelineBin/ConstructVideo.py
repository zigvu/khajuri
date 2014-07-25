#!/usr/bin/env python
import sys, os, time, pdb, glob, logging

from LogoPipeline import createDirIfNotExists
from Rectangle import Rectangle
from BoundingBoxes import BoundingBoxes
from ConfigReader import ConfigReader
from JSONReaderWriter import JSONReaderWriter
from PixelMapper import PixelMapper
from ImageManipulator import ImageManipulator
from ScaleSpaceCombiner import ScaleSpaceCombiner
from FramePostProcessor import FramePostProcessor
from CurationManager import CurationManager
from VideoWriter import VideoWriter

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../VideoReader'% baseScriptDir  )
import VideoReader

if __name__ == "__main__":
  if len( sys.argv ) < 5:
    print 'Usage %s <config.yaml> <video.file> <json.dir> <output.dir>' % sys.argv[ 0 ]
    sys.exit( 1 )
  configFileName = sys.argv[ 1 ]
  videoFileName = sys.argv[ 2 ]
  jsonFolder = sys.argv[ 3 ]
  outputFolder = sys.argv[ 4 ]

  createDirIfNotExists( outputFolder )

  configReader = ConfigReader(configFileName)
  videoFrameReader = VideoReader.VideoFrameReader( 40, 40, videoFileName )
  videoFrameReader.generateFrames()
  time.sleep( 1 )
  frame = videoFrameReader.getFrameWithFrameNumber( 1 )
  while not frame:
    frame = videoFrameReader.getFrameWithFrameNumber( 1 )
  imageDim = Rectangle.rectangle_from_dimensions( 
      frame.width,  
      frame.height )
  patchDimension = Rectangle.rectangle_from_dimensions(\
    configReader.sw_patchWidth, configReader.sw_patchHeight)
  staticBoundingBoxes = BoundingBoxes(imageDim, \
    configReader.sw_xStride, configReader.sw_xStride, patchDimension)

  fps = videoFrameReader.fps
  # we need frames in order
  frameIndex = {}
  jsonFiles = glob.glob(os.path.join(jsonFolder, "*json"))
  for jsonFileName in jsonFiles:
    print "Reading json " + os.path.basename(jsonFileName)
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    frameNumber = jsonReaderWriter.getFrameNumber()
    frameIndex[frameNumber] = jsonFileName
  print "Total of " + str(len(frameIndex.keys())) + " frames"
  classIds = JSONReaderWriter(jsonFiles[0]).getClassIds()
  # create video for each class - except background
  for classId in classIds:
    if classId in configReader.ci_backgroundClassIds:
      continue
    print "Working on video for class " + str(classId)
    videoFileName = os.path.join(outputFolder, "video_cls_" + str(classId) + ".avi")
    videoWriter = VideoWriter(videoFileName, fps, imageDim)
    frameNumber = 1
    while not videoFrameReader.eof or frameNumber <= videoFrameReader.totalFrames:
      frame = videoFrameReader.getFrameWithFrameNumber( int( frameNumber ) )
      while not frame:
        frame = videoFrameReader.getFrameWithFrameNumber( int( frameNumber ) )
      if frameNumber in sorted(frameIndex.keys()):
        jsonReaderWriter = JSONReaderWriter(frameIndex[frameNumber])
        framePostProcessor = FramePostProcessor(jsonReaderWriter, staticBoundingBoxes, configReader)
        framePostProcessor.run()
        lclzPixelMap = framePostProcessor.classPixelMaps[classId]['localizationMap']
      imageFileName = os.path.join(outputFolder, jsonReaderWriter.getFrameFileName())
      videoFrameReader.savePngWithFrameNumber(int(frameNumber), str( imageFileName) )
      imgLclz = ImageManipulator(imageFileName)
      imgLclz.addPixelMap(lclzPixelMap)
      for lclzPatch in jsonReaderWriter.getLocalizations(classId):
        bbox = Rectangle.rectangle_from_json(lclzPatch['bbox'])
        score = float(lclzPatch['score'])
        label = str(classId) + (": %.2f" % score)
        imgLclz.addLabeledBbox(bbox, label)
      videoWriter.addFrame(imgLclz)
      frameNumber += 1
      os.remove( imageFileName )
    videoWriter.save()
  print 'Done - ignore the core dump'
