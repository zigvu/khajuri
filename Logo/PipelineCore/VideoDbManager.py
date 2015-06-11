import os, shutil, re, time
from collections import OrderedDict
import json
import logging

from VideoReader import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

from config.Config import Config

class VideoDbManager( object ):
  """Class for extracting frames from video to db"""
  def __init__(self, config ):
    self.config = config
    self.scales = self.config.sw_scales
    self.maxProducedQueueSize = self.config.ci_lmdbBufferMaxSize
    self.compressedJSON = self.config.pp_compressedJSON
    
  def setupFolders(self, dbFolder, jsonFolder):
    """Setup folders"""
    # initializes the following:
    self.dbFolder = None
    self.jsonFolder = None

    self.dbFolder = dbFolder
    #config.mkdir_p(self.dbFolder) # this is made in C++    
    self.jsonFolder = jsonFolder
    Config.mkdir_p(self.jsonFolder)


  def setupVideoFrameReader(self, videoFileName):
    """Setup database creation from video given start of frame and steps"""
    # initializes the following:
    self.videoFrameReader = None
    self.staticBoundingBoxes = None
    self.totalNumOfFrames = None
    self.videoId = None
    self.imageDim = None

    # Load video
    self.videoFrameReader = VideoReader.VideoFrameReader(40, 40, videoFileName)
    self.videoFrameReader.generateFrames()
    if not self.config.logStarted:
      self.videoFrameReader.startLogger()
      self.config.logStarted = True

    # since no expilicit synchronization exists to check if
    # VideoReader is ready, wait for 10 seconds
    time.sleep(10)

    # Get frame dimensions and create bounding boxes
    frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    while not frame:
      frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    self.imageDim = Rectangle.rectangle_from_dimensions(frame.width, frame.height)
    patchDimension = Rectangle.rectangle_from_dimensions(\
      self.config.sw_patchWidth, self.config.sw_patchHeight)
    self.staticBoundingBoxes = BoundingBoxes(\
      self.imageDim, self.config.sw_xStride, self.config.sw_yStride, patchDimension)

    fps = self.videoFrameReader.fps
    lengthInMicroSeconds = self.videoFrameReader.lengthInMicroSeconds
    self.totalNumOfFrames = int(fps * lengthInMicroSeconds / 1000000.0)

    # Video name prefix for all frames/patches:
    self.videoId = os.path.basename(videoFileName).split('.')[0]


  def setupPrototxt(self, newPrototxtFile, deviceId):
    """Create new prototxt file to point to right db location
    Return: filename for new prototxt and new DB location"""
    # initializes the following:
    self.newPrototxtFile = None
    self.caffeBatchSize = 0
    self.deviceId = deviceId

    # create new prototxt
    prototxtFile = self.config.ci_video_prototxtFile
    self.newPrototxtFile = newPrototxtFile

    # calculate batch size from bounding boxes
    for scale in self.scales:
      self.caffeBatchSize += len(self.staticBoundingBoxes.getBoundingBoxes(scale))

    # if we want multiple frames per batch, change
    self.caffeBatchSize = self.caffeBatchSize * self.config.ci_lmdbNumFramesPerBuffer

    # ensure backend is lmdb
    isDbLMDB = False

    with open(prototxtFile) as fread:
      lines = fread.readlines()
    with open(self.newPrototxtFile, "w") as fwrite:
      for line in lines:
        if "source:" in line:
          line = line.replace(re.findall(r'\"(.+?)\"', line)[0], self.dbFolder)
        if "batch_size:" in line:
          line = line.replace(line.strip(" \n").split("batch_size: ")[1], str(self.caffeBatchSize))
        if "LMDB" in line:
          isDbLMDB = True
        fwrite.write("%s" % line)
    if not isDbLMDB:
      raise RuntimeError("Backend needs to be LMDB in prototxt file for VideoDbManager")


  def setupQueues(self, producedQueue, consumedQueue):
    """Setup queues"""
    self.producedQueue = producedQueue
    self.consumedQueue = consumedQueue


  def startVideoDb(self, frameStart, frameStep):
    """Save patches in video db"""
    # Initialize variables
    currentFrameNum = frameStart            # frame number being extracted
    dbPatchCounter = -1                     # total number of extracted patches
    dbBatchMapping = OrderedDict()          # mapping between patches in db and corresponding jsons
    dbBatchMappingFile = None               # temporary file to save mapping json
    dbBatchId = 0                           # number of db batches created

    videoDb = VideoReader.VideoDb(VideoReader.VideoDb.DBTYPE.LMDB, self.caffeBatchSize)
    videoDb.createNewDb(self.dbFolder, self.videoFrameReader)

    # Main loop to go through video
    logging.info("Start patch extraction for deviceId %d" % self.deviceId)
    while (not self.videoFrameReader.eof) or (currentFrameNum <= self.videoFrameReader.totalFrames):
      # For each batch of patches, put in queue
      if (((dbPatchCounter + 1) % self.caffeBatchSize) == 0):
        # add to db
        if len(dbBatchMapping) > 0:
          logging.debug("Saving batch ID: %d for device id %d" % (dbBatchId, self.deviceId))
          videoDb.saveDb()
          with open(dbBatchMappingFile, "w") as f :
            json.dump(dbBatchMapping, f, indent=2)
          self.producedQueue.put(dbBatchMappingFile)
          dbBatchId += 1

        # wait if caffe hasn't finished consuming
        if dbBatchId > self.maxProducedQueueSize:
          dbBatchMappingFileToDelete = self.consumedQueue.get()
          self.delFromVideoDb(videoDb, dbBatchMappingFileToDelete)
          self.consumedQueue.task_done()

        # reset datastructures
        dbBatchMapping = OrderedDict()
        dbBatchMappingFile = os.path.join(self.dbFolder, "db_mapping_%d.json" % dbBatchId)
        logging.info("%d percent video processed" % (int(100.0 * currentFrameNum/self.totalNumOfFrames)))

      # Start json annotation file
      jsonFile = os.path.join(self.jsonFolder, "%s_frame_%s.json" % (self.videoId, currentFrameNum))
      # Put patch into db
      patchNum = 0
      for scale in self.scales:
        for box in self.staticBoundingBoxes.getBoundingBoxes(scale):
          # Generate db patch and add to json
          dbPatchCounter = videoDb.savePatch(currentFrameNum, scale, \
            box[0], box[1], box[2], box [3])
          dbBatchMapping[dbPatchCounter] = { 'jsonFile' : jsonFile,
              'frameNum' : currentFrameNum, 'patchNum' : patchNum }
          # Increment counters
          patchNum += 1
      # Save annotation file
      currentFrameNum += frameStep
    # end while

    # For the last db group, save and put in queue
    if len(dbBatchMapping) > 0:
      logging.debug("Saving batch ID: %d for device id %d" % (dbBatchId, self.deviceId))
      videoDb.saveDb()
      with open(dbBatchMappingFile, "w") as f :
        json.dump(dbBatchMapping, f, indent=2)
      self.producedQueue.put(dbBatchMappingFile)

    # let consumer know that we are at the end
    self.producedQueue.put(None)
    # Put poison pills and wait to join all threads
    logging.info("Done with all patch extraction for device id %d" % self.deviceId)
    while True:
      dbBatchMappingFileToDelete = self.consumedQueue.get()
      # caffe finished evaluating
      if dbBatchMappingFileToDelete is None:
        self.consumedQueue.task_done()
        # poison pill means done with evaluations
        break
      # caffe evaluated
      self.delFromVideoDb(videoDb, dbBatchMappingFileToDelete)
      self.consumedQueue.task_done()

    logging.info("Waiting for videoFrameReader to exit gracefully")
    # HACK: work around so that videoDb releases lock on db folder
    videoDb = None
    # HACK: quit video reader gracefully
    currentFrameNum = self.videoFrameReader.totalFrames
    while not self.videoFrameReader.eof or currentFrameNum <= self.videoFrameReader.totalFrames:
      self.videoFrameReader.seekToFrameWithFrameNumber(currentFrameNum)
      currentFrameNum += 1


  def delFromVideoDb(self, videoDb, dbBatchMappingFileToDelete):
    """Delete all keys from VideoDb found in dbBatchMappingFileToDelete"""
    logging.debug("Deleting keys in file %s in deviceId %d" % (dbBatchMappingFileToDelete, self.deviceId))
    dbBatchMapping = json.load(open(dbBatchMappingFileToDelete, "r"))
    # delete patches
    for patchCounter, jsonFile in dbBatchMapping.iteritems():
      videoDb.deletePatch(int(patchCounter))
      videoDb.saveDb()
    # delete file
    Config.rm_rf(dbBatchMappingFileToDelete)
