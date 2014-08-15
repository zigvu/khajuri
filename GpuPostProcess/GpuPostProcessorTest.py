#!/usr/bin/python

import GpuPostProcessor
import cv2
import numpy as np

img = cv2.imread( "file.png" )
process = GpuPostProcessor.GpuPostProcessor( img )
for scale in [ 0.3, 0.5, 0.6, 0.8, 1.0, 1.2, 1.4 ]:
   process.resize( scale, scale )
   output = process.result
   cv2.imwrite( "file.resized.%s.png" % scale, output )
