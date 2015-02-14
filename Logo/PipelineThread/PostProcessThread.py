import sys, os, glob, time
from collections import OrderedDict
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager
import logging, pickle

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.FramePostProcessor import FramePostProcessor

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter
from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineMath.PixelMap import PixelMap
from Logo.PipelineCore.Version import LogoVersion

def framePostProcessorRun(sharedDict, postProcessQueue, allCellBoundariesDict):
  """Process for running post-processing of JSON outputs"""
  logging.info("Frame post processing thread started")
  configReader = ConfigReader(sharedDict['configFileName'])
  imageDim = Rectangle.rectangle_from_dimensions(sharedDict['image_width'], \
    sharedDict['image_height'])
  patchDimension = Rectangle.rectangle_from_dimensions(\
    configReader.sw_patchWidth, configReader.sw_patchHeight)
  staticBoundingBoxes = BoundingBoxes(imageDim, \
    configReader.sw_xStride, configReader.sw_yStride, patchDimension)
  numpyFolder = sharedDict['numpyFolder']
  while True:
    jsonFileName = postProcessQueue.get()
    if jsonFileName is None:
      postProcessQueue.task_done()
      # poison pill means done with json post processing
      break
    logging.debug("Start post processing of file %s" % jsonFileName)
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    framePostProcessor = FramePostProcessor(jsonReaderWriter, staticBoundingBoxes, configReader, allCellBoundariesDict)
    if framePostProcessor.run():
      # if dumping video heatmap, then save heatmap
      if configReader.ci_saveVideoHeatmap:
        frameNumber = jsonReaderWriter.getFrameNumber()
        numpyFileBaseName = os.path.join(numpyFolder, "%d" % frameNumber)
        framePostProcessor.saveLocalizations(numpyFileBaseName)
      postProcessQueue.task_done()
      logging.debug("Done post processing of file %s" % jsonFileName)

class PostProcessThread( object ):
  """Class responsible for post-processing caffe results"""
  def __init__(self, configFileName):
    """Initialize values"""
    self.configFileName = configFileName

    self.configReader = ConfigReader(configFileName)
    self.jsonFolder = self.configReader.sw_folders_json
    self.numpyFolder = self.configReader.sw_folders_numpy
    self.updateStatusSleepTime = 1

    if self.configReader.ci_saveVideoHeatmap:
      ConfigReader.mkdir_p(self.numpyFolder)

    # Logging levels
    logging.basicConfig(
      format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=self.configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")
    self.version = LogoVersion()

  def run( self ):
    """Run the video post processing"""
    logging.info("Setting up post-processing")
    self.version.logVersion()

    jsonFiles = glob.glob(os.path.join(self.jsonFolder, "*json")) + \
      glob.glob(os.path.join(self.jsonFolder, "*snappy"))
    
    tempJSONReaderWriter = JSONReaderWriter(jsonFiles[0])

    # Logging levels
    logging.basicConfig(
      format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=self.configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

    # Set up queues
    logging.info("Setting up post-processing queue")
    # Share state with other processes - since objects need ot be pickled
    # only put primitives where possible
    postProcessQueue = JoinableQueue()
    sharedManager = Manager()
    sharedDict = sharedManager.dict()
    sharedDict['configFileName'] = self.configFileName
    sharedDict['numpyFolder'] = self.numpyFolder
    sharedDict['image_width'] = tempJSONReaderWriter.getFrameWidth()
    sharedDict['image_height'] = tempJSONReaderWriter.getFrameHeight()

    scales = self.configReader.sw_scales
    imageDim = Rectangle.rectangle_from_dimensions(\
        sharedDict['image_width'], sharedDict['image_height'])
    patchDimension = Rectangle.rectangle_from_dimensions(\
        self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    staticBoundingBoxes = BoundingBoxes(imageDim, \
        self.configReader.sw_xStride, self.configReader.sw_yStride, patchDimension)
    scales = self.configReader.sw_scales
    allCellBoundariesDict = PixelMap.getCellBoundaries(staticBoundingBoxes, scales)

    # Start threads
    startTime = time.time()
    framePostProcesses = []
    num_consumers = max(int(self.configReader.multipleOfCPUCount * multiprocessing.cpu_count()), 1)
    #num_consumers = 1
    for i in xrange(num_consumers):
      framePostProcess = Process(target=framePostProcessorRun, args=(sharedDict, postProcessQueue\
          , allCellBoundariesDict ))
      framePostProcesses += [framePostProcess]
      framePostProcess.start()

    # Put JSON in queue so that workers can consume
    for jsonFileName in jsonFiles:
      logging.debug("Putting JSON file in queue: %s" % os.path.basename(jsonFileName))
      postProcessQueue.put(jsonFileName)

    logging.info("Done putting %d JSON files in queue - waiting for threads to join" % len(jsonFiles))

    while postProcessQueue.qsize() > 1:
      logging.info("Post processing %d percent done" % (int(100 - \
        100.0 * postProcessQueue.qsize()/len(jsonFiles))))
      time.sleep(self.updateStatusSleepTime)

    for i in xrange(num_consumers):
      postProcessQueue.put(None)
    postProcessQueue.join()
    logging.debug("Post-processing queue joined")
    for framePostProcess in framePostProcesses:
      framePostProcess.join()
    logging.debug("Post-processing process joined")
    logging.info("All post-processing tasks complete")

    endTime = time.time()
    logging.info( 'It took PostProcessThread %s seconds to complete' % ( endTime - startTime ) )

