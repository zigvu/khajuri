import os, glob, time
import logging

from Logo.PipelineMath.Rectangle import Rectangle

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter
from Logo.PipelineCore.ConfigReader import ConfigReader

class VideoLocalizationThread( object ):
  """Class to draw localization for all classes in video"""
  def __init__(self, configFileName, videoFileName):
    """Initialize values"""
    self.configReader = ConfigReader(configFileName)
    self.videoFileName = videoFileName
    self.jsonFolder = self.configReader.sw_folders_json
    self.videoOutputFolder = self.configReader.sw_folders_video

    ConfigReader.mkdir_p(self.videoOutputFolder)

    # Logging levels
    logging.basicConfig(format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s', 
      level=self.configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

  def run( self ):
    """Run the video through caffe"""
    startTime = time.time()
    logging.info("Setting up localization drawing for video %s" % self.videoFileName)

    videoFrameReader = VideoFrameReader(self.videoFileName)
    fps = videoFrameReader.getFPS()
    imageDim = videoFrameReader.getImageDim()

    # Read all JSONs
    frameIndex = {}
    jsonFiles = glob.glob(os.path.join(self.jsonFolder, "*json")) + \
      glob.glob(os.path.join(self.jsonFolder, "*snappy"))
    
    for jsonFileName in jsonFiles:
      logging.debug("Reading json %s" % os.path.basename(jsonFileName))
      jsonReaderWriter = JSONReaderWriter(jsonFileName)
      frameNumber = jsonReaderWriter.getFrameNumber()
      frameIndex[frameNumber] = jsonFileName
    logging.info("Total of %d json indexed" % len(frameIndex.keys()))

    # Set up output video
    videoBaseName = os.path.basename(self.videoFileName).split('.')[0]
    outVideoFileName = os.path.join(self.videoOutputFolder, "%s_localization.avi" % (videoBaseName))
    videoWriter = VideoWriter(outVideoFileName, fps, imageDim)

    # pre-fill video with frames that didn't get evaluated
    for currentFrameNum in range(0, self.configReader.ci_videoFrameNumberStart):
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
      if frame != None:
        # Save each frame
        imageFileName = os.path.join(self.videoOutputFolder, "temp_%d.png" % currentFrameNum)
        videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), str(imageFileName))
        imgLclz = ImageManipulator(imageFileName)
        # also add frame number label 
        bbox = Rectangle.rectangle_from_endpoints(1,1,250,35)
        label = "Frame: %d" % currentFrameNum
        imgLclz.addLabeledBbox(bbox, label)
        # Add to video and remove temp file
        videoWriter.addFrame(imgLclz)
        os.remove(imageFileName)

    # Go through evaluated video frame by frame
    currentFrameNum = self.configReader.ci_videoFrameNumberStart # frame number being extracted
    jsonReaderWriter = None
    frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
    while frame != None:
      logging.debug("Adding frame %d to video" % currentFrameNum)
      if currentFrameNum in frameIndex.keys():
        jsonReaderWriter = JSONReaderWriter(frameIndex[currentFrameNum])

      # Save each frame
      imageFileName = os.path.join(self.videoOutputFolder, "temp_%d.png" % currentFrameNum)
      videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), str(imageFileName))
      imgLclz = ImageManipulator(imageFileName)

      # Add bounding boxes
      for classId in self.configReader.ci_nonBackgroundClassIds:
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
      # Add to video and remove temp file
      videoWriter.addFrame(imgLclz)
      os.remove(imageFileName)
      # increment frame number
      currentFrameNum += 1
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))

    # Close video reader
    videoFrameReader.close()

    # Save and exit
    videoWriter.save()
    logging.info("Finished creating video")
    endTime = time.time()
    logging.info( 'It took VideoLocalizationThread %s seconds to complete' % ( endTime - startTime ) )
