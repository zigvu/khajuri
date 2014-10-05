#!/usr/bin/python

import sys, os, glob, time

from Logo.PipelineCommunication.CellrotiDetectables import CellrotiDetectables
from Logo.PipelineCommunication.DetectableClassMapper import DetectableClassMapper
from Logo.PipelineCore.ConfigReader import ConfigReader

if __name__ == '__main__':
  if len(sys.argv) < 5:
    print 'Usage %s <videoFileName> <mappingFileName> <jsonFolder> <outputFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  startTime = time.time()
  videoFileName = sys.argv[1]
  mappingFileName = sys.argv[2]
  jsonFolder = sys.argv[3]
  outputFolder = sys.argv[4]

  ConfigReader.mkdir_p(outputFolder)
  labeledLocalozationFileName = "%s/labeled_localization.json" % outputFolder

  cellrotiDetectables = CellrotiDetectables()
  cellrotiDetectables.read_mapped_detectables(mappingFileName)

  detectableClassMapper = DetectableClassMapper(videoFileName, jsonFolder, labeledLocalozationFileName, cellrotiDetectables)
  detectableClassMapper.run()
  endTime = time.time()
  print 'It took %s %s seconds to complete' % ( sys.argv[0], endTime - startTime )
