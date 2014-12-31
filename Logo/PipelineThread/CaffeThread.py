import os, time, sys
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager
from threading import Thread
from collections import OrderedDict
import json, pickle
import logging

import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.CaffeNet import CaffeNet

from Logo.PipelineThread.PostProcessThread import PostProcessThread
from Logo.PipelineThread.VideoReaderThread import VideoReaderThread
from Logo.PipelineThread.PostProcessThread import framePostProcessorRun
from Logo.PipelineMath.PixelMap import PixelMap
from Logo.PipelineCore.Version import LogoVersion

def caffeNetRun(sharedDict, leveldbQueue, postProcessQueue, deviceId):
  """Process for running caffe on a leveldb folder"""
  logging.info("Caffe thread started")
  configReader = ConfigReader(sharedDict['configFileName'])
  caffeNet = CaffeNet(configReader, deviceId)
  while True:
    curLeveldbFolder = leveldbQueue.get()
    if curLeveldbFolder is None:
      leveldbQueue.task_done()
      # poison pill means done with leveldb evaluation
      break
    logging.info("Caffe working on leveldb %s on device %s" % ( curLeveldbFolder, deviceId ) )
    # sleep some time so that file handles get cleared
    time.sleep(5)
    jsonFiles = caffeNet.run_net(curLeveldbFolder)
    if len(jsonFiles) > 0:
      logging.info("Finished processing curLeveldbFolder: %s" % curLeveldbFolder)
      # Running post-processor in parallel, enqueu json files
      if configReader.ci_runCaffePostProcessInParallel:
        logging.info("Enqueue JSON files for post-processing: %d" % len(jsonFiles))
        for jsonFile in jsonFiles:
          logging.debug("Putting JSON file in queue: %s" % os.path.basename(jsonFile))
          postProcessQueue.put(jsonFile)
      leveldbQueue.task_done()

class CaffeThread( object ):
  """Class responsible for starting and running caffe"""
  def __init__(self, configFileName, videoFileName, leveldbFolder, jsonFolder, numpyFolder):
    """Initialize values"""
    self.configFileName = configFileName
    self.configReader = ConfigReader(configFileName)
    self.videoFileName = videoFileName

    # Sliding window creation
    self.numConcurrentLeveldbs = self.configReader.ci_numConcurrentLeveldbs
    self.runPostProcessor = self.configReader.ci_runCaffePostProcessInParallel

    # Folder to save files
    self.leveldbFolder = leveldbFolder
    self.jsonFolder = jsonFolder
    self.numpyFolder = numpyFolder
    ConfigReader.rm_rf(self.leveldbFolder)
    ConfigReader.mkdir_p(self.leveldbFolder)
    ConfigReader.mkdir_p(self.jsonFolder)
    ConfigReader.mkdir_p(self.numpyFolder)
    # Logging levels
    logging.basicConfig(
      format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=self.configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

    # More than 1 GPU Available?
    self.gpu_devices = self.configReader.ci_gpu_devices
    self.version = LogoVersion()

  def run( self ):
    """Run the video through caffe"""
    startTime = time.time()
    self.version.logVersion()
    logging.info("Setting up caffe run for video %s" % self.videoFileName)
    if self.runPostProcessor:
      logging.info("Setting up post-processing to run in parallel")

    # Caffe: Setup producer/consumer queues
    leveldbQueue = JoinableQueue(self.numConcurrentLeveldbs)

    # Thread that spawns multiple VideoReader process for each GPU we have
    # in this system
    videoReaderThread = VideoReaderThread( leveldbQueue, self.leveldbFolder, self.jsonFolder,
        self.videoFileName, self.configReader, self.configReader.ci_videoFrameNumberStart )
    videoReaderThread.start()

    # Share state with other processes - since objects need ot be pickled
    # only put primitives where possible
    sharedManager = Manager()
    sharedDict = sharedManager.dict()
    sharedDict['configFileName'] = self.configFileName

    # Post processing: Setup
    postProcessQueue = JoinableQueue()
    framePostProcesses = []
    num_consumers = 0

    if self.runPostProcessor:
      sharedDict['numpyFolder'] = self.numpyFolder
      sharedDict['image_width'] = videoReaderThread.frame.width
      sharedDict['image_height'] = videoReaderThread.frame.height
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
      num_consumers = max(int(self.configReader.multipleOfCPUCount * multiprocessing.cpu_count()), 1)
      #num_consumers = 1
      for i in xrange(num_consumers):
        framePostProcess = Process(target=framePostProcessorRun, args=(sharedDict, postProcessQueue, allCellBoundariesDict))
        framePostProcesses += [framePostProcess]
        framePostProcess.start()
    caffeNetProcesses = []
    for gpuDevice in self.gpu_devices:
      caffeNetProcess = Process(target=caffeNetRun, args=(sharedDict, leveldbQueue, postProcessQueue, gpuDevice))
      caffeNetProcess.start()
      caffeNetProcesses.append( caffeNetProcess )

    logging.debug("Waiting for Caffe process to complete.")
    for caffeNetProcess in caffeNetProcesses:
      caffeNetProcess.join()
    videoReaderThread.join()
    leveldbQueue.join()
    logging.debug("Caffe process joined")

    # Join post-processing threads
    if self.runPostProcessor:
      logging.info("Waiting for post-processes to complete")
      for i in xrange(num_consumers):
        postProcessQueue.put(None)
      postProcessQueue.join()
      logging.debug("Post-processing queue joined")
      for framePostProcess in framePostProcesses:
        framePostProcess.join()
      logging.debug("Post-processing process joined")
      logging.info("All post-processing tasks complete")

    endTime = time.time()
    logging.info( 'It took CaffeThread %s seconds to complete' % ( endTime - startTime ) )
