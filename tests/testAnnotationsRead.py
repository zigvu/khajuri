#!/usr/bin/env python
from LogoPipeline import AnnotationsReader
import sys

if __name__ == '__main__':
  if len( sys.argv ) < 2:
    print 'Usage %s <json.file>' % sys.argv[ 0 ]
  else:
    reader = AnnotationsReader( sys.argv[ 1 ] )
    print reader.getAnnotationFileName()
    print reader.getFrameFileName()
    print reader.getFrameNumber()
    scalingFactors = reader.getScalingFactors()
    for scale in scalingFactors:
      print reader.getPatches( scale )
      print reader.getPatchFileNames( scale )
      print reader.getBoundingBoxes( scale )
    
