import sys, os, glob, time
from collections import OrderedDict
import logging

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.FramePostProcessor import FramePostProcessor

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineMath.PixelMap import PixelMap


class PostProcessManager( object ):
  """Class responsible for post-processing caffe results"""
  def __init__(self, configFileName):
    """Initialize values"""
    self.configFileName = configFileName

    self.configReader = ConfigReader(configFileName)
    self.saveHeatmap = self.configReader.ci_saveVideoHeatmap

  def setupFolders(self, numpyFolder):
    """Setup folders"""
    # initializes the following:
    self.numpyFolder = numpyFolder
    ConfigReader.mkdir_p(self.numpyFolder)

  def setupCells(self, imageWidth, imageHeight, allCellBoundariesDict):
    """Setup a static bounding box for this process workers to share"""
    # initializes the following:
    self.staticBoundingBoxes = None
    self.allCellBoundariesDict = None

    self.staticBoundingBoxes = PostProcessManager.getStaticBoundingBoxes(\
      self.configReader, imageWidth, imageHeight)
    self.allCellBoundariesDict = allCellBoundariesDict

  def setupQueues(self, postProcessQueue):
    """Setup queues"""
    self.postProcessQueue = postProcessQueue

  def startPostProcess(self):
    """Start post processing JSON until there are no more items in queue"""
    while True:
      jsonFileName = self.postProcessQueue.get()
      if jsonFileName is None:
        self.postProcessQueue.task_done()
        # poison pill means done with json post processing
        break
      logging.debug("Start post processing of file %s" % os.path.basename(jsonFileName))
      jsonReaderWriter = JSONReaderWriter(jsonFileName)
      framePostProcessor = FramePostProcessor(\
        jsonReaderWriter, self.staticBoundingBoxes, self.configReader, self.allCellBoundariesDict)
      if framePostProcessor.run():
        # if dumping video heatmap, then save numpy localizations
        if self.saveHeatmap:
          frameNumber = jsonReaderWriter.getFrameNumber()
          numpyFileBaseName = os.path.join(self.numpyFolder, "%d" % frameNumber)
          framePostProcessor.saveLocalizations(numpyFileBaseName)
        self.postProcessQueue.task_done()
        logging.debug("Done post processing of file %s" % os.path.basename(jsonFileName))


  @staticmethod
  def getAllCellBoundariesDict(configReader, imageWidth, imageHeight):
    staticBoundingBoxes = PostProcessManager.getStaticBoundingBoxes(\
      configReader, imageWidth, imageHeight)
    scales = configReader.sw_scales
    allCellBoundariesDict = PixelMap.getCellBoundaries(staticBoundingBoxes, scales)
    return allCellBoundariesDict

  @staticmethod
  def getStaticBoundingBoxes(configReader, imageWidth, imageHeight):
    """Get a bounding boxes object that can be shared"""
    imageDim = Rectangle.rectangle_from_dimensions(imageWidth, imageHeight)
    patchDimension = Rectangle.rectangle_from_dimensions(\
      configReader.sw_patchWidth, configReader.sw_patchHeight)
    staticBoundingBoxes = BoundingBoxes(imageDim, \
      configReader.sw_xStride, configReader.sw_yStride, patchDimension)
    return staticBoundingBoxes

