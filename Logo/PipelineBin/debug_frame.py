#!/usr/bin/python

import sys, os, glob, logging, re

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../../VideoReader'% baseScriptDir  )

from Logo.PipelineThread.VideoHeatmapThread import VideoHeatmapThread
from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter
from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.FramePostProcessor import FramePostProcessor
from Logo.PipelineMath.PixelMap import PixelMap


class FrameDebugger( object ):
  ''' Class to help debug a frame localizations '''
  def __init__(self, configFileName, videoFileName, jsonFolder,
      numpyFolder, outputFolder):
    self.configReader = ConfigReader(configFileName)
    self.videoFileName = videoFileName
    self.jsonFolder = jsonFolder
    self.numpyFolder = numpyFolder
    self.outputFolder = outputFolder
    self.videoFrameReader = VideoFrameReader(self.videoFileName)
    imageDim = self.videoFrameReader.getImageDim()
    patchDimension = Rectangle.rectangle_from_dimensions(\
        self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    self.staticBoundingBoxes = BoundingBoxes(imageDim, \
        self.configReader.sw_xStride, self.configReader.sw_yStride, patchDimension)
    scales = self.configReader.sw_scales
    self.allCellBoundariesDict = PixelMap.getCellBoundaries(self.staticBoundingBoxes, scales)

    ConfigReader.mkdir_p(self.outputFolder)
    # Logging levels
    logging.basicConfig(format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s', 
      level=self.configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

  def run( self, frameNum ):
    logging.debug( 'Starting to debug frame %s' % frameNum )
    logging.debug( 'Searching for frame %s in jsonFolder' % frameNum )
    jsonFiles = glob.glob(os.path.join(self.jsonFolder, "*json")) + \
      glob.glob(os.path.join(self.jsonFolder, "*snappy"))
    for jsonFileName in jsonFiles:
      m = re.match( '.*_frame_(\d+).json.*', jsonFileName )
      if str( frameNum ) == m.group(1):
        logging.debug( 'Found jsonFile %s' % jsonFileName )
        frame = self.videoFrameReader.getFrameWithFrameNumber(int(frameNum))
        jsonReaderWriter = JSONReaderWriter( jsonFileName )
        classIds = jsonReaderWriter.getClassIdsWithLocalizations()
        logging.debug( 'Post process frame for classId identfied in localizations' )
        framePostProcessor = FramePostProcessor(jsonReaderWriter, self.staticBoundingBoxes, self.configReader, self.allCellBoundariesDict )
        framePostProcessor.run()
        for classId in classIds:
          logging.debug( 'Processing classId %s in frameNum %s' % ( classId, frameNum ) )
          logging.debug( 'Show scale where localizations were identified' )
          print 'Best localization Scale is at %s for classId %s' % ( framePostProcessor.bestLocalizationScale[ classId ], classId )
          logging.debug( 'Dump heatmap frame for each classId identified in localizations' )
          if frame != None:
            imageFileName = os.path.join(self.outputFolder, "debug_%s_%s.png" % ( frameNum, classId ) )
            self.videoFrameReader.savePngWithFrameNumber(int(frameNum), str(imageFileName))
            image = ImageManipulator(imageFileName)
            bbox = Rectangle.rectangle_from_endpoints(1,1,250,35)
            label = "Frame: %d" % frameNum
            image.addLabeledBbox(bbox, label)
            image.addPixelMap( framePostProcessor.classPixelMaps[classId]['localizationMap'].toNumpyArray())
            for lclzPatch in jsonReaderWriter.getLocalizations(classId):
              bbox = Rectangle.rectangle_from_json(lclzPatch['bbox'])
              score = float(lclzPatch['score'])
              label = str(classId) + (": %.2f" % score)
              image.addLabeledBbox(bbox, label)
            localizationMap = framePostProcessor.classPixelMaps[classId]['localizationMap']
            for cb in localizationMap.cellBoundaries:
              bbox = Rectangle.rectangle_from_endpoints(
                  cb["x0"],
                  cb["y0"],
                  cb["x3"],
                  cb["y3"] )
              #image.addLabeledBbox( bbox, "")
              pass

            image.saveImage( imageFileName )


if __name__ == '__main__':
  if len(sys.argv) < 6:
    print 'Usage %s <config.yaml> <videoFileName> <jsonFolder> <numpyFolder> <outputFolder> <frameNum>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  jsonFolder = sys.argv[3]
  numpyFolder = sys.argv[4]
  outputFolder = sys.argv[5]
  frameNum = int( sys.argv[ 6 ] )

  frameDebugger = FrameDebugger(configFileName, videoFileName, jsonFolder,
      numpyFolder, outputFolder)
  frameDebugger.run( frameNum )



