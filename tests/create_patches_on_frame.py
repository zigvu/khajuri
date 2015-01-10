#!/usr/bin/env python
import sys, os, random, cv2

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../Logo' % baseScriptDir )

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.VideoWriter import VideoWriter

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

if __name__ == '__main__':
  if len( sys.argv ) < 5:
    print 'Usage %s outputFolder <config.yaml> videoWidth videoHeight' % sys.argv[ 0 ]
    sys.exit(1)

  print "Setting up Patches on Frames"

  outputFolder = sys.argv[1]
  configReader = ConfigReader( sys.argv[ 2 ] )
  videoWidth = int(sys.argv[3])
  videoHeight = int(sys.argv[4])
  imageDim = Rectangle.rectangle_from_dimensions(videoWidth, videoHeight) # 1280, 720
  patchDim = Rectangle.rectangle_from_dimensions(\
    configReader.sw_patchWidth, configReader.sw_patchHeight)
  staticBoundingBoxes = BoundingBoxes(imageDim, \
    configReader.sw_xStride, configReader.sw_yStride, patchDim)
  cornerBoxWH = 10


  ConfigReader.mkdir_p(outputFolder)

  # Create a blank image
  totalPatches = 0
  for scale in configReader.sw_scales:
    blankImageFilename = os.path.join(outputFolder, "blank_image_%s.png" % scale )
    os.system("convert -size %dx%d xc:blue %s"
                % (imageDim.width * scale , imageDim.height * scale, blankImageFilename))
    img = cv2.imread( blankImageFilename )
    for box in set( staticBoundingBoxes.getBoundingBoxes(scale) ):
      bbox = Rectangle.rectangle_from_endpoints( box[ 0 ], box[ 1 ],
                                              box[ 0 ] + box[ 2 ], box[ 1 ] + box [ 3 ] )
      colorForeground = (0,0,256)
      pts = bbox.cv2_format()
      cv2.polylines( img, [pts - 1], True, colorForeground)
      cv2.imwrite( blankImageFilename, img )
      totalPatches += 1
  print 'Total Patches : %s' % totalPatches
