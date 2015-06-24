import os, glob, time

from Logo.PipelineMath.Rectangle import Rectangle

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter

from config.Config import Config

from postprocessing.task.JsonReader import JsonReader


class VideoLocalizationThread(object):
  """Class to draw localization for all classes in video"""

  def __init__(self, configFileName, videoFileName, jsonFolder,
               videoOutputFolder):
    """Initialize values"""
    self.config = Config(configFileName)
    self.logger = self.config.logger

    self.videoFileName = videoFileName
    self.jsonFolder = jsonFolder
    self.videoOutputFolder = videoOutputFolder

    # TODO: remove - currently this is a bug which causes
    # JSONReader to crash
    self.config.videoId = 1

    self.jsonReader = JsonReader(self.config, None)

    Config.mkdir_p(self.videoOutputFolder)


  def run(self):
    """Run the video through caffe"""
    startTime = time.time()
    self.logger.info(
        "Setting up localization drawing for video %s" % self.videoFileName)

    videoFrameReader = VideoFrameReader(self.videoFileName)
    fps = videoFrameReader.getFPS()
    imageDim = videoFrameReader.getImageDim()

    # Read all JSONs
    frameIndex = {}
    jsonFiles = glob.glob(os.path.join(self.jsonFolder, "*json"))

    for jsonFileName in jsonFiles:
      self.logger.debug("Reading json %s" % os.path.basename(jsonFileName))
      frameObj = self.jsonReader(jsonFileName)[0]
      frameNumber = frameObj.frameNumber
      frameIndex[frameNumber] = jsonFileName
    self.logger.info("Total of %d json files indexed" % len(frameIndex.keys()))

    self.logger.info("Creating new video")
    # Set up output video
    videoBaseName = os.path.basename(self.videoFileName).split('.')[0]
    outVideoFileName = os.path.join(
        self.videoOutputFolder, "%s_localization.avi" % (videoBaseName))
    videoWriter = VideoWriter(outVideoFileName, fps, imageDim)

    # pre-fill video with frames that didn't get evaluated
    for currentFrameNum in range(0, self.config.ci_videoFrameNumberStart):
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
      if frame != None:
        # Save each frame
        imageFileName = os.path.join(
            self.videoOutputFolder, "temp_%d.png" % currentFrameNum)
        videoFrameReader.savePngWithFrameNumber(
            int(currentFrameNum), str(imageFileName))
        imgLclz = ImageManipulator(imageFileName)
        # also add frame number label
        bbox = Rectangle.rectangle_from_endpoints(1, 1, 250, 35)
        label = "Frame: %d" % currentFrameNum
        imgLclz.addLabeledBbox(bbox, label)
        # Add to video and remove temp file
        videoWriter.addFrame(imgLclz)
        os.remove(imageFileName)

    # Go through evaluated video frame by frame

    # frame number being extracted
    currentFrameNum = self.config.ci_videoFrameNumberStart
    frameObj = None
    frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
    while frame != None:
      self.logger.debug("Adding frame %d to video" % currentFrameNum)
      if currentFrameNum in frameIndex.keys():
        frameObj = self.jsonReader(frameIndex[currentFrameNum])[0]

      # Save each frame
      imageFileName = os.path.join(
          self.videoOutputFolder, "temp_%d.png" % currentFrameNum)
      videoFrameReader.savePngWithFrameNumber(
          int(currentFrameNum), str(imageFileName))
      imgLclz = ImageManipulator(imageFileName)

      # Add bounding boxes
      for classId, lclzPatches in frameObj.localizations.iteritems():
        for lclzPatch in lclzPatches:
          rect = lclzPatch.rect
          bbox = Rectangle.rectangle_from_endpoints(
              rect.x, rect.y, rect.x + rect.w, rect.y + rect.h)
          score = lclzPatch.score
          label = str(classId) + (": %.2f" % score)
          imgLclz.addLabeledBbox(bbox, label)
      # also add frame number label - indicate if scores from this frame
      bbox = Rectangle.rectangle_from_endpoints(1, 1, 250, 35)
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
    self.logger.info("Finished creating video")
    endTime = time.time()
    self.logger.info('It took VideoLocalizationThread %s seconds to complete' %
                 (endTime - startTime))
