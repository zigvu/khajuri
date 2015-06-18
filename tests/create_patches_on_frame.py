#!/usr/bin/env python
import sys, os, random, cv2

from config.Config import Config

from Logo.PipelineCore.VideoWriter import VideoWriter

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

if __name__ == '__main__':
  if len(sys.argv) < 4:
    print 'Usage %s ' % sys.argv[0] + \
      '<outputFolder> <videoWidth> <videoHeight>'
    sys.exit(1)

  print "Setting up Patches on Frames"

  outputFolder = sys.argv[1]
  videoWidth = int(sys.argv[2])
  videoHeight = int(sys.argv[3])
  # 1280, 720
  imageDim = Rectangle.rectangle_from_dimensions(videoWidth, videoHeight)
  patchDim = Rectangle.rectangle_from_dimensions(
      configReader.sw_patchWidth, configReader.sw_patchHeight)
  staticBoundingBoxes = BoundingBoxes(imageDim, configReader.sw_xStride,
                                      configReader.sw_yStride, patchDim)
  cornerBoxWH = 10

  Config.mkdir_p(outputFolder)

  # Create a blank image
  totalPatches = 0
  for scale in configReader.sw_scales:
    blankImageFilename = os.path.join(
        outputFolder, "blank_image_%s.png" % scale)
    os.system("convert -size %dx%d xc:blue %s" % (
        imageDim.width * scale, imageDim.height * scale, blankImageFilename
    ))
    img = cv2.imread(blankImageFilename)
    for box in set(staticBoundingBoxes.getBoundingBoxes(scale)):
      bbox = Rectangle.rectangle_from_endpoints(
          box[0], box[1], box[0] + box[2], box[1] + box[3])
      colorForeground = (0, 0, 256)
      pts = bbox.cv2_format()
      cv2.polylines(img, [pts - 1], True, colorForeground)
      cv2.imwrite(blankImageFilename, img)
      totalPatches += 1
  print 'Total Patches : %s' % totalPatches
