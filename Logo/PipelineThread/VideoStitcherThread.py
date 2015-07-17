import os, time, json
import multiprocessing
from multiprocessing import JoinableQueue, Process

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter

from config.Config import Config
from config.Utils import Utils


def runAviToMp4Converter(conversionQueue):
  """Process to convert avi to mp4 file"""
  while True:
    clipFileName = conversionQueue.get()
    if clipFileName is None:
      conversionQueue.task_done()
      # poison pill means done with clip conversion
      break
    # print("Start mp4 conversion of file %s" % os.path.basename(clipFileName))

    # Set up output clip
    aviFolder = os.path.dirname(clipFileName)
    aviFile = os.path.basename(clipFileName).split('.')[0]
    mp4FileName = os.path.join(aviFolder, "%s.mp4" % (aviFile))

    # exec call
    os.system("ffmpeg -i %s %s" % (clipFileName, mp4FileName))
    os.remove(clipFileName)
    conversionQueue.task_done()
    # print("Done mp4 conversion of file %s" % os.path.basename(clipFileName))


class VideoSitcherThread(object):
  """Class to combine frames from multiple videos into clips"""

  def __init__(self, configFileName):
    """Initialize values"""
    self.config = Config(configFileName)

    self.jobCfg = self.config.job
    self.logger = self.config.logging.logger
    self.caffeInputCfg = self.config.caffeInput
    self.storageCfg = self.config.storage

    # job details
    self.zigvuJobId = self.jobCfg.zigvuJobId
    self.kheerJobId = self.jobCfg.kheerJobId
    self.sticthDetails = self.jobCfg.sticthDetails
    self.numContextFramesBefore = self.jobCfg.numContextFramesBefore
    self.numContextFramesAfter = self.jobCfg.numContextFramesAfter

    self.clipsOutputFolder = self.storageCfg.clipFolder
    Utils.mkdir_p(self.clipsOutputFolder)
    self.tempFolder = os.path.join(
        '/mnt/tmp', os.path.basename(videoFileName).split('.')[0])
    Utils.mkdir_p(self.tempFolder)

    self.numFrameInClip = self.storageCfg.hdf5ClipFrameCount


  def run(self):
    """Stitch frames from multiple videos into clips"""
    startTime = time.time()
    self.logger.info("Setting up stitch for kheer job id %s" % self.kheerJobId)

    # keep track of frame numbers for each clip
    videoClipsMap = {}

    # conversion threads
    conversionQueue = JoinableQueue()
    conversionProcesses = []
    # num_consumers = 1
    num_consumers = multiprocessing.cpu_count()

    for i in xrange(num_consumers):
      conversionProcess = Process(
          target=runAviToMp4Converter,
          args=(conversionQueue,))
      conversionProcesses += [conversionProcess]
      conversionProcess.start()

    # clip number
    clipId = 0
    clipWriter = None
    outClipFileName = None
    currentNumberOfFramesInClip = 0

    for videoId in self.sticthDetails.keys():
      videoDetails = self.sticthDetails[videoId]
      videoFileName = videoDetails['url']
      videoFrameNumbers = self.frameNumbersToExtract(
          sorted(videoDetails['frames']))

      videoFrameReader = VideoFrameReader(videoFileName)
      fps = videoFrameReader.getFPS()
      imageDim = videoFrameReader.getImageDim()

      currentFrameNum = 0  # frame number being extracted

      frame = videoFrameReader.getFrameWithFrameNumber(
          int(self.caffeInputCfg.ci_videoFrameNumberStart))
      while frame != None:
        if (currentNumberOfFramesInClip >= self.numFrameInClip):
          if clipWriter != None:
            # close clip and kick off mp4 conversion
            clipWriter.save()
            conversionQueue.put(outClipFileName)
            videoClipsMap[clipId]['frame_number_end'] = (currentFrameNum - 1)
            clipId += 1
          self.logger.debug("Creating new clip id: %d" % clipId)
          outClipFileName = os.path.join(
              self.clipsOutputFolder, "%d.avi" % clipId)
          clipWriter = VideoWriter(outClipFileName, fps, imageDim)
          currentNumberOfFramesInClip = 0
          videoClipsMap[clipId] = {
              'clip_filename': "%d.mp4" % clipId,
              'frame_number_start': currentFrameNum
          }

        self.logger.debug("Adding frame %d to video" % currentFrameNum)
        # Save each frame
        imageFileName = os.path.join(
            self.tempFolder, "temp_%d.png" % currentFrameNum)
        videoFrameReader.savePngWithFrameNumber(
            int(currentFrameNum), str(imageFileName))
        imgManipulator = ImageManipulator(imageFileName)
        # Add to clip and remove temp file
        imgManipulator.embedFrameNumber(currentFrameNum % self.numFrameInClip)
        clipWriter.addFrame(imgManipulator)
        os.remove(imageFileName)
        # increment frame number
        currentFrameNum += 1
        frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))

      # Close video reader
      videoFrameReader.close()
    # done with all videos

    # close last clip writer
    if clipWriter != None:
      # close clip and kick off mp4 conversion
      clipWriter.save()
      conversionQueue.put(outClipFileName)
      videoClipsMap[clipId]['frame_number_end'] = (currentFrameNum - 1)

    # write map file
    with open(self.videoClipsMapFilename, "w") as f:
      json.dump(videoClipsMap, f, indent=2)

    # join conversion threads
    self.logger.info("Waiting for mp4 conversion threads to complete")
    for i in xrange(num_consumers):
      conversionQueue.put(None)
    conversionQueue.join()
    self.logger.debug("Mp4 conversion queues joined")
    for conversionProcess in conversionProcesses:
      conversionProcess.join()
    self.logger.debug("Mp4 conversion processes joined")

    # Exit
    self.logger.info("Finished creating clips")
    endTime = time.time()
    self.logger.info(
        'It took VideoSplitterThread %s seconds to complete' %
        (endTime - startTime))


  def frameNumbersToExtract(videoFrameNumbers):
    newVideoFrameNumbers = []
    for videoFN in videoFrameNumbers:
      videoFNBegin = videoFN - self.numContextFramesBefore
      if videoFNBegin < self.caffeInputCfg.ci_videoFrameNumberStart:
        videoFNBegin = self.caffeInputCfg.ci_videoFrameNumberStart
      videoFNEnd = videoFN + self.numContextFramesAfter
      newVideoFrameNumbers += range(videoFNBegin, videoFNEnd + 1)
    return newVideoFrameNumbers
