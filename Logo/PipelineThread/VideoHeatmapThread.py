import sys, os, glob, time
from collections import OrderedDict
import logging, re
import multiprocessing
from threading import Thread
import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.PixelMap import PixelMap

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter
from Logo.PipelineCore.ConfigReader import ConfigReader

from multiprocessing import JoinableQueue, Process, Manager

global cells
cells = None

def saveFrameToVideo( argumentsQueue, s ):
  while True:
    startTime = time.time()
    arg = argumentsQueue.get()
    logging.info( ' %s waiting for argument for %s' % ( os.getpid(), time.time() - startTime ) )
    if not arg:
      argumentsQueue.task_done()
      break
    else:
      videoFrame, lclzPixelMaps, \
      jsonReaderWriter, classId, currentFrameNum, frameIndex, videoHeatMap, lastClass = \
          arg
      imgLclz = ImageManipulator(None, videoFrame)
      pixelMap = PixelMap( cells, 1.0 )
      pixelMap.cellValues = lclzPixelMaps[( currentFrameNum, classId)]
      numpyPixelMap = pixelMap.toNumpyArray()
      imgLclz.addPixelMap( numpyPixelMap )
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
      videoHeatMap[currentFrameNum] = imgLclz
      #if lastClass:
      #  os.remove( imageFileName )
      argumentsQueue.task_done()

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
    logging.basicConfig(format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s', 
      level=self.configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

  def startPool( self ):
    self.manager = multiprocessing.Manager()
    # Start processes
    self.processes = []
    self.pool = multiprocessing.Pool()
    self.argumentsQueue = JoinableQueue()
    for i in range( 0, int ( 0.5 * multiprocessing.cpu_count() ) ):
      p = Process( target=saveFrameToVideo, args=( self.argumentsQueue, None ) )
      self.processes.append( p )
      p.start()

  
  def join( self ):
    logging.info('Waiting for processes to complete' )
    self.argumentsQueue.join()
    for p in self.processes:
      p.join()

  def getFrameIndex( self ):
    frameIndex = {}
    jsonFiles = glob.glob(os.path.join(self.jsonFolder, "*json")) + \
      glob.glob(os.path.join(self.jsonFolder, "*snappy"))
    
    for jsonFileName in jsonFiles:
      m = re.match( ".*_frame_(\d+).json.*", jsonFileName )
      if m:
        frameIndex[ int( m.group( 1 ) ) ] = jsonFileName
      else:
        assert False, '%s fileName unexpected' % jsonFileName

    logging.info("Total of %d json indexed" % len(frameIndex.keys()))
    return frameIndex

  def run( self ):
    """Run the video through caffe"""
    startTime = time.time()
    logging.info("Setting up heatmap drawing for video %s" % self.videoFileName)
    frameIndex = self.getFrameIndex()

    # Start reading video
    logging.info("Creating videos")
    videoFrameReader = VideoFrameReader(self.videoFileName)
    fps = videoFrameReader.getFPS()
    imageDim = videoFrameReader.getImageDim()
    patchDimension = Rectangle.rectangle_from_dimensions(\
        self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    staticBoundingBoxes = BoundingBoxes(imageDim, \
        self.configReader.sw_xStride, self.configReader.sw_yStride, patchDimension)
    scales = self.configReader.sw_scales
    self.allCellBoundariesDict = PixelMap.getCellBoundaries(staticBoundingBoxes, scales)
    global cells
    cells = self.allCellBoundariesDict
    self.startPool()

    # Create as many output videos as non background classes
    videoBaseName = os.path.basename(self.videoFileName).split('.')[0]
    videoHeatMaps = {}
    videoWriters = {}
    for classId in self.configReader.ci_heatMapClassIds:
      videoHeatMaps[classId] = self.manager.dict()
      outVideoFileName = os.path.join(self.videoOutputFolder, \
        "%s_%s.avi" % (videoBaseName, str(classId)))
      logging.debug("Videos to create: %s with frames %s" % ( outVideoFileName,
        len( videoHeatMaps[ classId ].keys() ) ) )
      videoWriter = VideoWriter(outVideoFileName, fps, imageDim)
      videoWriter.frames = videoHeatMaps[ classId ]
      videoWriters[ classId ] = videoWriter


    # pre-fill video with frames that didn't get evaluated
    lastSavedVideoFrame = 0
    for currentFrameNum in range(0, self.configReader.ci_videoFrameNumberStart):
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
      if frame != None:
        # Save each frame
        imageFileName = os.path.join(self.videoOutputFolder, "temp_%d.png" % currentFrameNum )
        videoFrame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
        for classId in self.configReader.ci_heatMapClassIds:
          imgLclz = ImageManipulator(None, videoFrame)
          bbox = Rectangle.rectangle_from_endpoints(1,1,250,35)
          label = "Frame: %d" % currentFrameNum
          imgLclz.addLabeledBbox(bbox, label)
          videoHeatMaps[classId][currentFrameNum] = imgLclz
        #os.remove(imageFileName)

    # Go through evaluated video frame by frame
    jsonReaderWriter = None
    lclzPixelMaps = {}
    currentFrameNum = self.configReader.ci_videoFrameNumberStart
    frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
    frameIndexKeys = frameIndex.keys()

    while frame != None:
      #logging.debug("Adding frame %d to video" % currentFrameNum)
      startTime = time.time()
      if currentFrameNum in frameIndexKeys:
        jsonReaderWriter = JSONReaderWriter(frameIndex[currentFrameNum])
        numpyFileBaseName = os.path.join(self.numpyFolder, "%d" % currentFrameNum)
        for classId in self.configReader.ci_heatMapClassIds:
          clsFilename = "%s_%s.npy" % (numpyFileBaseName, str(classId))
          #logging.info( 'Adding into lclzPixelMaps, ( %s, %s )' % (
          #  currentFrameNum, classId ) )
          lclzPixelMaps[( currentFrameNum, classId )] = np.load(clsFilename)
      else:
        for classId in self.configReader.ci_heatMapClassIds:
          lclzPixelMaps[( currentFrameNum, classId )] = \
              lclzPixelMaps[( currentFrameNum - 1, classId )]
      #logging.info( 'Setting up numpy took %s seconds' % ( time.time() - startTime ) )

      # Save each frame
      imageFileName = os.path.join(self.videoOutputFolder, "temp_%d.png" % currentFrameNum )
      videoFrame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))

      for classId in self.configReader.ci_heatMapClassIds:
        self.argumentsQueue.put( 
          ( videoFrame,
          lclzPixelMaps, jsonReaderWriter,
          classId,
          currentFrameNum, frameIndex, videoHeatMaps[classId],
          classId == self.configReader.ci_heatMapClassIds[ -1 ] )
          )
        if currentFrameNum - lastSavedVideoFrame > 10:
          for classId in self.configReader.ci_heatMapClassIds:
            videoWriter = videoWriters[ classId ]
            videoWriter.save()
            lastSavedVideoFrame = currentFrameNum

      # increment frame number
      currentFrameNum += 1
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
      endTime = time.time()
      #logging.info( 'Rest took %s seconds' % ( time.time() - startTime ) )
      #logging.info( 'Frame %s took %s seconds' % ( currentFrameNum, ( endTime - startTime ) ) )
    # Close video reader
    videoFrameReader.close()

    logging.debug("Saving heatmap videos")
    # Once video is done, save all files
    for classId in self.configReader.ci_heatMapClassIds:
      videoWriters[classId].save() 
      videoWriters[classId].close() 
    logging.info("Finished creating videos")
    endTime = time.time()
    logging.info( 'It took VideoHeatmapThread %s seconds to complete' % ( endTime - startTime ) )
