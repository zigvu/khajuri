#!/usr/bin/env python
import sys, os, random

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../Logo' % baseScriptDir )

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter

from Logo.PipelineMath.Rectangle import Rectangle

if __name__ == '__main__':
  if len( sys.argv ) < 5:
    print 'Usage %s outputFolder numOfFrames videoWidth videoHeight' % sys.argv[ 0 ]
    sys.exit(1)

  print "Setting up video creator"

  outputFolder = sys.argv[1]
  numOfFrames = int(sys.argv[2])
  videoWidth = int(sys.argv[3])
  videoHeight = int(sys.argv[4])
  fps = 25
  imageDim = Rectangle.rectangle_from_dimensions(videoWidth, videoHeight) # 1280, 720
  cornerBoxWH = 10


  ConfigReader.mkdir_p(outputFolder)

  # Create a blank image
  blankImageFilename = os.path.join(outputFolder, "blank_image.png")
  os.system("convert -size %dx%d xc:blue %s" % (imageDim.width, imageDim.height, blankImageFilename))

  # start video writer
  videoFileName = os.path.join(outputFolder, "out.avi")
  videoWriter = VideoWriter(videoFileName, fps, imageDim)

  # put in for loop to create all frames
  for i in xrange(0, numOfFrames):
    print "Adding frame %d" % i
    img = ImageManipulator(blankImageFilename)
    # write frame number
    bbox = Rectangle.rectangle_from_endpoints(imageDim.width/2 - 100, 0, imageDim.width/2 + 100, 50)
    label = "Frame: %d" % i
    img.addLabeledBbox(bbox, label)
    # add corners to video
    bbox = Rectangle.rectangle_from_endpoints(0, 0, cornerBoxWH, cornerBoxWH)
    img.addLabeledBbox(bbox, "")
    bbox = Rectangle.rectangle_from_endpoints(imageDim.width - cornerBoxWH, 0, imageDim.width, cornerBoxWH)
    img.addLabeledBbox(bbox, "")
    bbox = Rectangle.rectangle_from_endpoints(imageDim.width - cornerBoxWH, imageDim.height - cornerBoxWH, imageDim.width, imageDim.height)
    img.addLabeledBbox(bbox, "")
    bbox = Rectangle.rectangle_from_endpoints(0, imageDim.height - cornerBoxWH, cornerBoxWH, imageDim.height)
    img.addLabeledBbox(bbox, "")
    # write 4 random boxes:
    for j in xrange(0, 4):
      rwS = random.randint(cornerBoxWH, imageDim.width - cornerBoxWH - 100)
      rhS = random.randint(cornerBoxWH, imageDim.height - cornerBoxWH - 50)
      bbox = Rectangle.rectangle_from_endpoints(rwS, rhS, rwS + 100, rhS + 50)
      label = "[%d, %d, %d, %d]" % (rwS, rhS, rwS + 100, rhS + 50)
      img.addLabeledBbox(bbox, label)
    # write to video
    videoWriter.addFrame(img)


  # clean up
  videoWriter.save()
  if os.path.exists(blankImageFilename):
    os.remove(blankImageFilename)

  print "Finished creating file %s" % videoFileName
