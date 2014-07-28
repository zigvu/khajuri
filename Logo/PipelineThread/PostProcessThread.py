import sys, os, glob
from collections import OrderedDict
from multiprocessing import JoinableQueue, Process, Manager
import logging
import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.FramePostProcessor import FramePostProcessor

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter
from Logo.PipelineCore.ConfigReader import ConfigReader

def framePostProcessorRun(sharedDict, postProcessQueue):
  """Process for running post-processing of JSON outputs"""
  logging.info("Frame post processing thread started")
  configReader = ConfigReader(sharedDict['configFileName'])
  imageDim = Rectangle.rectangle_from_dimensions(sharedDict['image_width'], \
    sharedDict['image_height'])
  patchDimension = Rectangle.rectangle_from_dimensions(\
    configReader.sw_patchWidth, configReader.sw_patchHeight)
  staticBoundingBoxes = BoundingBoxes(imageDim, \
    configReader.sw_xStride, configReader.sw_xStride, patchDimension)
  numpyFolder = sharedDict['numpyFolder']
  while True:
    jsonFileName = postProcessQueue.get()
    if jsonFileName is None:
      postProcessQueue.task_done()
      # poison pill means done with json post processing
      break
    logging.debug("Start post processing of file %s" % jsonFileName)
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    framePostProcessor = FramePostProcessor(jsonReaderWriter, staticBoundingBoxes, configReader)
    if framePostProcessor.run():
      # if dumping video heatmap, then save heatmap
      if configReader.ci_saveVideoHeatmap:
        frameNumber = jsonReaderWriter.getFrameNumber()
        numpyFileName = os.path.join(numpyFolder, "%d.npz" % frameNumber)
        framePostProcessor.saveLocalizations(numpyFileName)
      postProcessQueue.task_done()
      logging.debug("Done post processing of file %s" % jsonFileName)

class PostProcessThread( object ):
  """Class responsible for post-processing caffe results"""
  def __init__(self, configFileName, videoFileName, jsonFolder, outputFolder):
    """Initialize values"""
    self.configFileName = configFileName
    self.videoFileName = videoFileName
    self.jsonFolder = jsonFolder
    self.outputFolder = outputFolder

    self.configReader = ConfigReader(configFileName)

    # Logging levels
    logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
      level=self.configReader.log_level)

  def run( self ):
    """Run the video post processing"""
    logging.info("Setting up post-processing for video %s" % self.videoFileName)


    numpyFolder = os.path.join(self.outputFolder, self.configReader.sw_folders_numpy)
    ConfigReader.mkdir_p(numpyFolder)
    jsonFiles = glob.glob(os.path.join(self.jsonFolder, "*json"))
    tempJSONReaderWriter = JSONReaderWriter(jsonFiles[0])

    # Logging levels
    logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
      level=self.configReader.log_level)

    # Set up queues
    logging.info("Setting up post-processing queue")
    # Share state with other processes - since objects need ot be pickled
    # only put primitives where possible
    postProcessQueue = JoinableQueue()
    sharedManager = Manager()
    sharedDict = sharedManager.dict()
    sharedDict['configFileName'] = self.configFileName
    sharedDict['numpyFolder'] = numpyFolder
    sharedDict['image_width'] = tempJSONReaderWriter.getFrameWidth()
    sharedDict['image_height'] = tempJSONReaderWriter.getFrameHeight()

    # Start threads
    framePostProcesses = []
    #num_consumers = multiprocessing.cpu_count()
    num_consumers = 1
    for i in xrange(num_consumers):
      framePostProcess = Process(target=framePostProcessorRun, args=(sharedDict, postProcessQueue))
      framePostProcesses += [framePostProcess]
      framePostProcess.start()

    # Put JSON in queue so that workers can consume
    for jsonFileName in jsonFiles:
      logging.debug("Putting JSON file in queue: %s" % os.path.basename(jsonFileName))
      postProcessQueue.put(jsonFileName)

    logging.info("Put all JSON files in queue - waiting for threads to join")
    for i in xrange(num_consumers):
      postProcessQueue.put(None)
    postProcessQueue.join()
    logging.debug("Post-processing queue joined")
    for framePostProcess in framePostProcesses:
      framePostProcess.join()
    logging.debug("Post-processing process joined")

    # Re-read JSONs and verify that localization patches got created
    logging.debug("Verifying all localizations got created")
    frameIndex = {}
    for jsonFileName in jsonFiles:
      logging.debug("Verifying localization in file %s" % jsonFileName)
      jsonReaderWriter = JSONReaderWriter(jsonFileName)
      frameNumber = jsonReaderWriter.getFrameNumber()
      frameIndex[frameNumber] = jsonFileName
      # this access will raise KeyError if localization not computed
      localizationSanityCheck = jsonReaderWriter.getLocalizations(\
        self.configReader.ci_nonBackgroundClassIds[0])
    logging.debug("Verified: all localizations got created")

    # If creating heatmap video
    if self.configReader.ci_saveVideoHeatmap:
      logging.info("Creating heat map videos")

      videoFrameReader = VideoFrameReader(self.videoFileName)
      fps = videoFrameReader.getFPS()
      imageDim = videoFrameReader.getImageDim()

      # Create as many output videos as non background classes
      self.videoOutputFolder = os.path.join(self.outputFolder, self.configReader.sw_folders_video)
      ConfigReader.mkdir_p(self.videoOutputFolder)
      videoBaseName = os.path.basename(self.videoFileName).split('.')[0]
      videoHeatMaps = OrderedDict()
      for classId in self.configReader.ci_nonBackgroundClassIds:
        outVideoFileName = os.path.join(self.videoOutputFolder, \
          "%s_%s.avi" % (videoBaseName, str(classId)))
        logging.debug("Videos to create: %s" % outVideoFileName)
        videoHeatMaps[classId] = VideoWriter(outVideoFileName, fps, imageDim)

      # Go through video frame by frame
      currentFrameNum = self.configReader.ci_videoFrameNumberStart # frame number being extracted
      jsonReaderWriter = None
      lclzPixelMaps = None
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
      while frame != None:
        logging.debug("Adding frame %d to video" % currentFrameNum)
        if currentFrameNum in frameIndex.keys():
          jsonReaderWriter = JSONReaderWriter(frameIndex[currentFrameNum])
          numpyFileName = os.path.join(numpyFolder, "%d.npz" % currentFrameNum)
          lclzPixelMaps = np.load(numpyFileName)

        # Save each frame
        imageFileName = os.path.join(self.videoOutputFolder, "temp_%d.png" % currentFrameNum)
        videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), str(imageFileName))

        # Add heatmap and bounding boxes    
        for classId in self.configReader.ci_nonBackgroundClassIds:
          imgLclz = ImageManipulator(imageFileName)
          imgLclz.addPixelMap(lclzPixelMaps[classId])
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
      for classId in self.configReader.ci_nonBackgroundClassIds:
        videoHeatMaps[classId].save()
      logging.info("Finished creating video")

    # Done
    logging.info("All post-processing tasks done successfully")
