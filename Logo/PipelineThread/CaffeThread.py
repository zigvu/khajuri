import os, time
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager
from threading import Thread
from collections import OrderedDict
import json
import logging

import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.CaffeNet import CaffeNet

from Logo.PipelineThread.PostProcessThread import PostProcessThread
from Logo.PipelineThread.PostProcessThread import framePostProcessorRun

def caffeNetRun(sharedDict, leveldbQueue, postProcessQueue):
  """Process for running caffe on a leveldb folder"""
  logging.info("Caffe thread started")
  configReader = ConfigReader(sharedDict['configFileName'])
  caffeNet = CaffeNet(configReader)
  while True:
    curLeveldbFolder = leveldbQueue.get()
    if curLeveldbFolder is None:
      leveldbQueue.task_done()
      # poison pill means done with leveldb evaluation
      break
    logging.info("Caffe working on leveldb %s" % curLeveldbFolder)
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

class VideoReaderThread( Thread ):
  """ Class for extracting frames from video """
  def __init__( self, leveldbQueue, leveldbFolder, jsonFolder, videoFileName, configReader, frameStartNum ):
    super(VideoReaderThread, self).__init__()
    self.leveldbQueue = leveldbQueue
    self.leveldbFolder = leveldbFolder
    self.jsonFolder = jsonFolder
    self.videoFileName = videoFileName
    self.configReader = configReader
    self.scales = self.configReader.sw_scales
    self.frameStep = self.configReader.sw_frame_density
    self.videoFrameReader = VideoReader.VideoFrameReader(40, 40, self.videoFileName)
    self.videoFrameReader.generateFrames()
    self.videoFrameReader.startLogger()

    # Load video - since no expilicit synchronization exists to check if
    # VideoReader is ready, wait for 10 seconds
    time.sleep(10)

    # Get frame dimensions and create bounding boxes
    self.frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    while not self.frame:
      self.frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    self.imageDim = Rectangle.rectangle_from_dimensions(self.frame.width, self.frame.height)
    self.patchDimension = Rectangle.rectangle_from_dimensions(\
      self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    self.staticBoundingBoxes = BoundingBoxes(self.imageDim, \
      self.configReader.sw_xStride, self.configReader.sw_xStride, self.patchDimension)

    self.fps = self.videoFrameReader.fps
    self.lengthInMicroSeconds = self.videoFrameReader.lengthInMicroSeconds
    self.totalNumOfFrames = int(self.fps * self.lengthInMicroSeconds / 1000000.0)

    #self.startFrameNumber = self.configReader.ci_videoFrameNumberStart
    self.startFrameNumber = frameStartNum
    self.numFramesPerLeveldb = self.configReader.ci_numFramesPerLeveldb
    self.leveldbFolderSize = self.configReader.ci_maxLeveldbSizeMB

    # Video name prefix for all frames/patches:
    self.videoId = os.path.basename(videoFileName).split('.')[0]
 
  def run( self ):
    """ Spawn as many processes as there are GPUs"""
    p = Process( target=startVideoReaderProcess, args={self} )
    p.start()

def startVideoReaderProcess( self ):
  """ Run the VideoReader Thread """
  # Initialize variables
  currentFrameNum = self.startFrameNumber # frame number being extracted
  extractedFrameCounter = 0               # total number of extracted frames
  curLeveldbFolder = None                 # folder where to write leveldb
  videoLeveldb = None                     # levedb object from VideoReader
  leveldbMapping = None                   # mapping between patches in leveldb and corresponding jsons
  leveldbId = 0                           # number of leveldb created

  videoFrameReader = VideoReader.VideoFrameReader(40, 40, self.videoFileName)
  videoFrameReader.generateFrames()

  # Load video - since no expilicit synchronization exists to check if
  # VideoReader is ready, wait for 10 seconds
  time.sleep(10)
  
  # Main loop to go through video
  logging.info("Start patch extraction")
  while (not videoFrameReader.eof) or (currentFrameNum <= videoFrameReader.totalFrames):
    # Create new leveldbs for each set of numFramesPerLeveldb frames
    if ((extractedFrameCounter %  self.numFramesPerLeveldb) == 0):
      # If ready, save leveldb and put in queue for CaffeNet
      if videoLeveldb != None:
        logging.info("Saving leveldb ID: %d" % (leveldbId))
        videoLeveldb.saveLevelDb()
        with open(leveldbMappingFile, "w") as f :
          json.dump(leveldbMapping, f, indent=2)
        # sleep some time so that file handles get cleared
        time.sleep(5)
        self.leveldbQueue.put(curLeveldbFolder)
      # If leveldb folder is full, wait until dump
      if self.leveldbFolderSize > 0:
        leveldbFolderSize = ConfigReader.dir_size(self.leveldbFolder)
        while leveldbFolderSize >= self.leveldbFolderSize:
          logging.info("Waiting for leveldb folder to empty")
          time.sleep(5)
          leveldbFolderSize = ConfigReader.dir_size(self.leveldbFolder)
      # Set up new levedb
      extractedFrameCounter = 0
      leveldbPatchCounter = 0
      curLeveldbFolder = os.path.join(self.leveldbFolder, "%s_leveldb_%d" % (self.videoId, leveldbId))
      leveldbMappingFile = os.path.join(curLeveldbFolder, "leveldb_mapping.json")
      videoLeveldb = VideoReader.VideoLevelDb(curLeveldbFolder)
      videoLeveldb.setVideoFrameReader(videoFrameReader)
      leveldbMapping = OrderedDict()
      leveldbId += 1
      logging.info("%d percent video processed" % (int(100.0 * currentFrameNum/self.totalNumOfFrames)))
    # Start json annotation file
    jsonName = os.path.join(self.jsonFolder, "%s_frame_%s.json" % (self.videoId, currentFrameNum))
    jsonAnnotation = JSONReaderWriter(jsonName, create_new=True)
    jsonAnnotation.initializeJSON(self.videoId, currentFrameNum, self.imageDim, self.scales)
    # Put patch into leveldb
    for scale in self.scales:
      patchNum = 0
      for box in self.staticBoundingBoxes.getBoundingBoxes(scale):
        # Generate leveldb patch and add to json
        leveldbPatchCounter = videoLeveldb.savePatch(currentFrameNum, scale, \
          box[0], box[1], box[2], box [3])
        jsonAnnotation.addPatch(scale, patchNum, leveldbPatchCounter, \
          box[0], box[1], box[2], box [3])
        leveldbMapping[leveldbPatchCounter] = jsonName
        # Increment counters
        patchNum += 1
    # Save annotation file
    jsonAnnotation.saveState()
    logging.debug("Finished working on frame %d" % currentFrameNum)
    currentFrameNum += self.frameStep
    extractedFrameCounter += 1
  # end while

  # For the last leveldb group, save and put in queue
  if videoLeveldb != None:
    logging.info("Saving leveldb ID: %d" % (leveldbId))
    videoLeveldb.saveLevelDb()
    with open(leveldbMappingFile, "w") as f :
      json.dump(leveldbMapping, f, indent=2)
    self.leveldbQueue.put(curLeveldbFolder)

  # HACK: work around so that VideoLevelDb releases lock on curLeveldbFolder
  videoLeveldb = None
  # HACK: quit video reader gracefully
  currentFrameNum = videoFrameReader.totalFrames
  while not videoFrameReader.eof or currentFrameNum <= videoFrameReader.totalFrames:
    videoFrameReader.seekToFrameWithFrameNumber(currentFrameNum)
    currentFrameNum += 1

  # Put poison pills and wait to join all threads
  logging.info("Done with all patch extraction. Waiting for caffe thread to join")
  self.leveldbQueue.put(None)
  self.leveldbQueue.join()

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
    logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
      level=self.configReader.log_level)

  def run( self ):
    """Run the video through caffe"""
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
      # Start threads
      num_consumers = max(int(self.configReader.multipleOfCPUCount * multiprocessing.cpu_count()), 1)
      #num_consumers = 1
      for i in xrange(num_consumers):
        framePostProcess = Thread(target=framePostProcessorRun, args=(sharedDict, postProcessQueue))
        framePostProcesses += [framePostProcess]
        framePostProcess.start()

    caffeNetProcess = Thread(target=caffeNetRun, args=(sharedDict, leveldbQueue, postProcessQueue))
    caffeNetProcess.start()

    logging.debug("Caffe queue joined")
    caffeNetProcess.join()
    videoReaderThread.join()
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

      # Verification
      logging.debug("Verifying all localizations got created")
      PostProcessThread.verifyLocalizations(self.jsonFolder, self.configReader.ci_nonBackgroundClassIds[0])
      
      logging.info("All post-processing tasks complete")
