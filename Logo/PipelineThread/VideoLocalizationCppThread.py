import os, glob, time, sys
import logging

from Logo.PipelineMath.Rectangle import Rectangle
# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/VideoReader'% baseScriptDir  )
import VideoReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter
from Logo.PipelineCore.ConfigReader import ConfigReader

class VideoLocalizationCppThread( object ):
  """Class to draw localization for all classes in video"""
  def __init__(self, configFileName, videoFileName, jsonFolder, videoOutputFolder):
    """Initialize values"""
    self.configReader = ConfigReader(configFileName)
    self.videoFileName = videoFileName
    self.jsonFolder = jsonFolder
    self.videoOutputFolder = videoOutputFolder

    ConfigReader.mkdir_p(self.videoOutputFolder)

    # Logging levels
    logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
      level=self.configReader.log_level)

  def run( self ):
    """Run the video through caffe"""
    startTime = time.time()
    logging.info("Setting up localization drawing for video %s" % self.videoFileName)

    videoFrameReader = VideoReader.VideoFrameReader( 40, 40, self.videoFileName)
    videoFrameReader.generateFrames()
    time.sleep( 5 )
    fps = videoFrameReader.fps

    # Read all JSONs
    frameIndex = {}
    jsonFiles = glob.glob(os.path.join(self.jsonFolder, "*json"))
    for jsonFileName in jsonFiles:
      logging.debug("Reading json %s" % os.path.basename(jsonFileName))
      jsonReaderWriter = JSONReaderWriter(jsonFileName)
      frameNumber = jsonReaderWriter.getFrameNumber()
      frameIndex[frameNumber] = jsonFileName
    logging.info("Total of %d json indexed" % len(frameIndex.keys()))

    # Set up output video
    videoBaseName = os.path.basename(self.videoFileName).split('.')[0]
    outVideoFileName = os.path.join(self.videoOutputFolder, "%s_localization.avi" % (videoBaseName))
    videoAnnotator = VideoReader.VideoFrameAnnotator( outVideoFileName )
    videoAnnotator.setVideoFrameReader( videoFrameReader )

    # pre-fill video with frames that didn't get evaluated
    for currentFrameNum in range(0, self.configReader.ci_videoFrameNumberStart):
      videoAnnotator.addBoundingBox( currentFrameNum, 0, 0, 0, 0, 0, 0 )

    # Go through evaluated video frame by frame
    currentFrameNum = self.configReader.ci_videoFrameNumberStart # frame number being extracted
    jsonReaderWriter = None
    done = False
    while not done:
      if videoFrameReader.eof and currentFrameNum > videoFrameReader.totalFrames:
        logging.debug( 'Finished creating video.' )
        done = True
      else:
        logging.debug("Adding frame %d to video" % currentFrameNum)
        if currentFrameNum in frameIndex.keys():
          jsonReaderWriter = JSONReaderWriter(frameIndex[currentFrameNum])

        # Add bounding boxes
        for classId in self.configReader.ci_nonBackgroundClassIds:
          for lclzPatch in jsonReaderWriter.getLocalizations(classId):
            bbox = Rectangle.rectangle_from_json(lclzPatch['bbox'])
            score = float(lclzPatch['score'])
            label = str(classId) + (": %.2f" % score)
            videoAnnotator.addBoundingBox( currentFrameNum, int(bbox.x0), int(bbox.y0), bbox.width, bbox.height, int( classId ), score )
        # increment frame number
        videoAnnotator.addToVideo( currentFrameNum, currentFrameNum in frameIndex.keys() )
        currentFrameNum += 1

    endTime = time.time()
    logging.info( 'It took VideoLocalizationThread %s seconds to complete' % ( endTime - startTime ) )
