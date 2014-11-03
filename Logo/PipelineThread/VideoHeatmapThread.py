import sys, os, glob, time
from collections import OrderedDict
import logging
import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.PixelMap import PixelMap

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter
from Logo.PipelineCore.ConfigReader import ConfigReader

class VideoHeatmapThread( object ):
  """Class to draw heatmap for all classes in video"""
  def __init__(self, configFileName, videoFileName, jsonFolder, numpyFolder, videoOutputFolder):
    """Initialize values"""
    self.configReader = ConfigReader(configFileName)
    self.videoFileName = videoFileName
    self.jsonFolder = jsonFolder
    self.numpyFolder = numpyFolder
    self.videoOutputFolder = videoOutputFolder

    ConfigReader.mkdir_p(self.videoOutputFolder)

    # Check for config.yaml file's save_heatmap and curation

    # Logging levels
    logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
      level=self.configReader.log_level)

  def run( self ):
    """Run the video through caffe"""
    startTime = time.time()
    logging.info("Setting up heatmap drawing for video %s" % self.videoFileName)

    # Read all JSONs
    frameIndex = {}
    jsonFiles = glob.glob(os.path.join(self.jsonFolder, "*json"))
    for jsonFileName in jsonFiles:
      logging.debug("Reading json %s" % os.path.basename(jsonFileName))
      jsonReaderWriter = JSONReaderWriter(jsonFileName)
      frameNumber = jsonReaderWriter.getFrameNumber()
      frameIndex[frameNumber] = jsonFileName
    logging.info("Total of %d json indexed" % len(frameIndex.keys()))

    # Start reading video
    logging.info("Creating videos")
    videoFrameReader = VideoFrameReader(self.videoFileName)
    fps = videoFrameReader.getFPS()
    imageDim = videoFrameReader.getImageDim()
    patchDimension = Rectangle.rectangle_from_dimensions(\
        self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    staticBoundingBoxes = BoundingBoxes(imageDim, \
        self.configReader.sw_xStride, self.configReader.sw_xStride, patchDimension)
    scales = self.configReader.sw_scales
    self.allCellBoundariesDict = PixelMap.getCellBoundaries(staticBoundingBoxes, scales)

    # Create as many output videos as non background classes
    videoBaseName = os.path.basename(self.videoFileName).split('.')[0]
    videoHeatMaps = OrderedDict()
    for classId in self.configReader.ci_heatMapClassIds:
      outVideoFileName = os.path.join(self.videoOutputFolder, \
        "%s_%s.avi" % (videoBaseName, str(classId)))
      logging.debug("Videos to create: %s" % outVideoFileName)
      videoHeatMaps[classId] = VideoWriter(outVideoFileName, fps, imageDim)

    # pre-fill video with frames that didn't get evaluated
    for currentFrameNum in range(0, self.configReader.ci_videoFrameNumberStart):
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
      if frame != None:
        # Save each frame
        imageFileName = os.path.join(self.videoOutputFolder, "temp_%d.png" % currentFrameNum)
        videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), str(imageFileName))
        for classId in self.configReader.ci_heatMapClassIds:
          imgLclz = ImageManipulator(imageFileName)
          bbox = Rectangle.rectangle_from_endpoints(1,1,250,35)
          label = "Frame: %d" % currentFrameNum
          imgLclz.addLabeledBbox(bbox, label)
          videoHeatMaps[classId].addFrame(imgLclz)
        os.remove(imageFileName)

    # Go through evaluated video frame by frame
    jsonReaderWriter = None
    lclzPixelMaps = {}
    currentFrameNum = self.configReader.ci_videoFrameNumberStart
    frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
    while frame != None:
      logging.debug("Adding frame %d to video" % currentFrameNum)
      if currentFrameNum in frameIndex.keys():
        jsonReaderWriter = JSONReaderWriter(frameIndex[currentFrameNum])
        numpyFileBaseName = os.path.join(self.numpyFolder, "%d" % currentFrameNum)
        lclzPixelMaps = {}
        for classId in self.configReader.ci_heatMapClassIds:
          clsFilename = "%s_%s.npy" % (numpyFileBaseName, str(classId))
          lclzPixelMaps[classId] = np.load(clsFilename)

      # Save each frame
      imageFileName = os.path.join(self.videoOutputFolder, "temp_%d.png" % currentFrameNum)
      videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), str(imageFileName))

      # Add heatmap and bounding boxes    
      for classId in self.configReader.ci_heatMapClassIds:
        imgLclz = ImageManipulator(imageFileName)
        pixelMap = PixelMap( self.allCellBoundariesDict, 1.0 )
        pixelMap.cellValues = lclzPixelMaps[classId]
        imgLclz.addPixelMap( pixelMap.toNumpyArray() )
        for lclzPatch in jsonReaderWriter.getLocalizations(classId):
          bbox = Rectangle.rectangle_from_json(lclzPatch['bbox'])
          score = float(lclzPatch['score'])
          label = str(classId) + (": %.2f" % score)
          imgLclz.addLabeledBbox(bbox, label)
        # also add frame number label - indicate if scores from this frame
        bbox = Rectangle.rectangle_from_endpoints(1,1,250,35)
        label = "Frame: %d" % currentFrameNum
        if currentFrameNum in frameIndex.keys():
          label = "Frame: %d*" % currentFrameNum
        imgLclz.addLabeledBbox(bbox, label)
        videoHeatMaps[classId].addFrame(imgLclz)

      os.remove(imageFileName)
      # increment frame number
      currentFrameNum += 1
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))

    # Close video reader
    videoFrameReader.close()

    logging.debug("Saving heatmap videos")
    # Once video is done, save all files
    for classId in self.configReader.ci_heatMapClassIds:
      videoHeatMaps[classId].save()
    logging.info("Finished creating videos")
    endTime = time.time()
    logging.info( 'It took VideoHeatmapThread %s seconds to complete' % ( endTime - startTime ) )
