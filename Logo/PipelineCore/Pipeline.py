import os, time
import json
from collections import OrderedDict
import multiprocessing
from multiprocessing import Queue, JoinableQueue, Process, Manager
from Queue import PriorityQueue
import logging

import VideoReader
from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.FramePostProcessor import FramePostProcessor

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.CaffeNet import CaffeNet
from Logo.PipelineCore.VideoHeatMapper import VideoHeatMapper

def videoHeatMapperRun(sharedDict, videoHeatMapperQueue):
  """Process for creating heat map video"""
  logging.info("VideoHeatMapper thread started")
  configReader = ConfigReader(sharedDict['configFileName'])
  videoFileName = sharedDict['videoFileName']
  videoOutputFolder = sharedDict['videoOutputFolder']
  videoHeatMapper = VideoHeatMapper(configReader, videoFileName, videoOutputFolder, videoHeatMapperQueue)
  videoHeatMapper.run()

def framePostProcessorRun(sharedDict, postProcessQueue, videoHeatMapperQueue):
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
      if configReader.ci_saveVideoHeatmap:
        # put poison pill
        videoHeatMapperQueue.put("PoisonPill")
      postProcessQueue.task_done()
      # poison pill means done with json post processing
      break
    logging.debug("Start post processing of file %s" % jsonFileName)
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    framePostProcessor = FramePostProcessor(jsonReaderWriter, staticBoundingBoxes, configReader)
    if framePostProcessor.run():
      # if dumping video heatmap, then put in queue
      if configReader.ci_saveVideoHeatmap:
        frameNumber = jsonReaderWriter.getFrameNumber()
        numpyFileName = os.path.join(numpyFolder, "%d.npz" % frameNumber)
        framePostProcessor.saveLocalizations(numpyFileName)
        videoHeatMapperQueue.put((frameNumber, [jsonFileName, numpyFileName]))
      logging.debug("Done post processing of file %s" % jsonFileName)
      postProcessQueue.task_done()

def caffeNetRun(sharedDict, leveldbQueue, postProcessQueue):
  """Process for running caffe on a leveldb folder"""
  logging.info("Caffe thread started")
  configReader = ConfigReader(sharedDict['configFileName'])
  caffeNet = CaffeNet(configReader, postProcessQueue)
  while True:
    levedbFolder = leveldbQueue.get()
    if levedbFolder is None:
      leveldbQueue.task_done()
      # poison pill means done with leveldb evaluation
      break
    logging.info("Caffe working on leveldb %s" % levedbFolder)
    if caffeNet.run_net(levedbFolder):
      logging.info("Finished processing levedbFolder: %s" % levedbFolder)
      leveldbQueue.task_done()

class Pipeline( object ):
  """Main class for pipeline of running logo
     In separate processes, this class 
     (a) creates leveldb of patches from video,
     (b) evaluates leveldb through caffe
     (c) analyses caffe output per frame in post-processing step
  """
  def __init__(self, configFileName, videoFileName, outputDir):
    """Initialize values"""
    self.configFileName = configFileName
    self.configReader = ConfigReader(configFileName)
    self.videoFileName = videoFileName

    # Sliding window creation
    self.frameStep = self.configReader.sw_frame_density
    self.scales = self.configReader.sw_scales
    self.numFramesPerLeveldb = self.configReader.ci_numFramesPerLeveldb
    self.numConcurrentLeveldbs = self.configReader.ci_numConcurrentLeveldbs
    self.startFrameNumber = self.configReader.ci_videoFrameNumberStart

    # Folder to save files
    self.outputFramesDir = os.path.join(outputDir, self.configReader.sw_folders_frame)
    self.outputJsonDir = os.path.join(outputDir, self.configReader.sw_folders_annotation)
    self.outputLeveldbDir = os.path.join(outputDir, self.configReader.sw_folders_leveldb)
    self.videoOutputFolder = os.path.join(outputDir, self.configReader.sw_folders_video)
    self.numpyFolder = os.path.join(outputDir, self.configReader.sw_folders_numpy)
    ConfigReader.mkdir_p(self.outputFramesDir)
    ConfigReader.mkdir_p(self.outputJsonDir)
    ConfigReader.mkdir_p(self.outputLeveldbDir)
    ConfigReader.mkdir_p(self.videoOutputFolder)
    ConfigReader.mkdir_p(self.numpyFolder)

    # Video name prefix for all frames/patches:
    self.videoId = os.path.basename(videoFileName).split('.')[0]

    # Logging levels
    logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
      level=self.configReader.log_level)

  def run( self ):
    """Run the pipeline"""
    logging.info("Setting up pipeline for video %s" % self.videoFileName)

    # Load video - since no expilicit synchronization exists to check if
    # VideoReader is ready, wait for 10 seconds
    videoFrameReader = VideoReader.VideoFrameReader(40, 40, self.videoFileName)
    videoFrameReader.generateFrames()
    time.sleep(10)

    # Get frame dimensions and create bounding boxes
    frame = videoFrameReader.getFrameWithFrameNumber(1)
    while not frame:
      frame = videoFrameReader.getFrameWithFrameNumber(1)
    imageDim = Rectangle.rectangle_from_dimensions(frame.width, frame.height)
    patchDimension = Rectangle.rectangle_from_dimensions(\
      self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    staticBoundingBoxes = BoundingBoxes(imageDim, \
      self.configReader.sw_xStride, self.configReader.sw_xStride, patchDimension)

    # Share state with other processes - since objects need ot be pickled
    # only put primitives where possible
    sharedManager = Manager()
    sharedDict = sharedManager.dict()
    sharedDict['configFileName'] = self.configFileName
    sharedDict['image_width'] = frame.width
    sharedDict['image_height'] = frame.height
    sharedDict['videoFileName'] = self.videoFileName
    sharedDict['videoOutputFolder'] = self.videoOutputFolder
    sharedDict['numpyFolder'] = self.numpyFolder

    # Setup producer/consumer queues - since objects need to be pickled
    # only put primitives where possible
    leveldbQueue = JoinableQueue(self.numConcurrentLeveldbs)
    postProcessQueue = JoinableQueue()
    videoHeatMapperQueue = JoinableQueue()
    caffeNetProcess = Process(target=caffeNetRun, args=(sharedDict, leveldbQueue, postProcessQueue))
    caffeNetProcess.start()

    # Post processing - reserve 2 processor to run frame extraction and caffe
    framePostProcesses = []
    num_consumers = max(multiprocessing.cpu_count() - 2, 1)
    #num_consumers = 1
    for i in xrange(num_consumers):
      framePostProcess = Process(target=framePostProcessorRun, args=(sharedDict, \
        postProcessQueue, videoHeatMapperQueue))
      framePostProcesses += [framePostProcess]
      framePostProcess.start()
    # Video heatmap
    if self.configReader.ci_saveVideoHeatmap:
      videoHeatMapperProcess = Process(target=videoHeatMapperRun, args=(sharedDict, videoHeatMapperQueue))
      videoHeatMapperProcess.start()

    # Initialize variables
    currentFrameNum = self.startFrameNumber # frame number being extracted
    extractedFrameCounter = 0               # total number of extracted frames
    leveldbPatchCounter = 0                 # for each leveldb, counter of patches inside it
    levedbFolder = None                     # folder where to write leveldb
    videoLeveldb = None                     # levedb object from VideoReader
    leveldbMapping = None                   # mapping between patches in leveldb and corresponding jsons
    leveldbId = 0                           # number of leveldb created
    
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
          leveldbQueue.put(levedbFolder)
        # Set up new levedb
        extractedFrameCounter = 0
        leveldbPatchCounter = 0
        levedbFolder = os.path.join(self.outputLeveldbDir, "%s_leveldb_%d" % (self.videoId, leveldbId))
        leveldbMappingFile = os.path.join(levedbFolder, "leveldb_mapping.json")
        videoLeveldb = VideoReader.VideoLevelDb(levedbFolder)
        videoLeveldb.setVideoFrameReader(videoFrameReader)
        leveldbMapping = OrderedDict()
        leveldbId += 1
        logging.info("%d percent video processed" % (int(100.0 * currentFrameNum/videoFrameReader.totalFrames)))
        logging.info("Q sizes: leveldbQueue: %d, postProcessQueue: %d, videoHeatMapperQueue: %d" % \
          (leveldbQueue.qsize(), postProcessQueue.qsize(), videoHeatMapperQueue.qsize()))
      # Start json annotation file
      jsonName = os.path.join(self.outputJsonDir, "%s_frame_%s.json" % (self.videoId, currentFrameNum))
      jsonAnnotation = JSONReaderWriter(jsonName, create_new=True)
      jsonAnnotation.initializeJSON(self.videoId, currentFrameNum, self.scales)
      # Put patch into leveldb
      for scale in self.scales:
        patchNum = 0
        for box in staticBoundingBoxes.getBoundingBoxes(scale):
          # Generate leveldb
          videoLeveldb.savePatch(currentFrameNum, scale, box[0], box[1], box[2], box [3])
          # Add patch to annotation file
          jsonAnnotation.addPatch(scale, patchNum, leveldbPatchCounter, box[0], box[1], box[2], box [3])
          leveldbMapping[leveldbPatchCounter] = jsonName
          # Increment counters
          patchNum += 1
          leveldbPatchCounter += 1
      # Save annotation file
      jsonAnnotation.saveState()
      currentFrameNum += self.frameStep
      extractedFrameCounter += 1
      logging.debug("Finished working on frame %d, Patch %d" % (currentFrameNum, leveldbPatchCounter))
    # end while

    # For the last leveldb group, save and put in queue
    if videoLeveldb != None:
      logging.info("Saving leveldb ID: %d" % (leveldbId))
      videoLeveldb.saveLevelDb()
      with open(leveldbMappingFile, "w") as f :
        json.dump(leveldbMapping, f, indent=2)
      leveldbQueue.put(levedbFolder)

    # HACK: work around so that VideoLevelDb releases lock on levedbFolder
    videoLeveldb = None
    # HACK: quit video reader gracefully
    currentFrameNum = videoFrameReader.totalFrames
    while not videoFrameReader.eof or currentFrameNum <= videoFrameReader.totalFrames:
      videoFrameReader.seekToFrameWithFrameNumber(currentFrameNum)
      currentFrameNum += 1

    # Put poison pills and wait to join all threads
    logging.info("Done with all patch extraction. Waiting for threads to join")
    leveldbQueue.put(None)
    leveldbQueue.join()
    logging.debug("Caffe queue joined")
    for i in xrange(num_consumers):
      postProcessQueue.put(None)
    postProcessQueue.join()
    logging.debug("Post-processing queue joined")
    videoHeatMapperQueue.join() # poison pill put in post-process thread
    logging.debug("VideoHeatMapper queue joined")
    # join processes
    caffeNetProcess.join()
    logging.debug("Caffe process joined")
    for framePostProcess in framePostProcesses:
      framePostProcess.join()
    logging.debug("Post-processing process joined")
    if self.configReader.ci_saveVideoHeatmap:
      videoHeatMapperProcess.join()
    logging.debug("VideoHeatMapper process joined")
    logging.info("Joined all threads")
