import os, time, json
import multiprocessing
from multiprocessing import JoinableQueue, Process
import logging

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter

from config.Config import Config


def runAviToMp4Converter(conversionQueue):
  """Process to convert avi to mp4 file"""
  while True:
    clipFileName = conversionQueue.get()
    if clipFileName is None:
      conversionQueue.task_done()
      # poison pill means done with clip conversion
      break
    logging.debug(
        "Start mp4 conversion of file %s" % os.path.basename(clipFileName))

    # Set up output clip
    aviFolder = os.path.dirname(clipFileName)
    aviFile = os.path.basename(clipFileName).split('.')[0]
    mp4FileName = os.path.join(aviFolder, "%s.mp4" % (aviFile))

    # exec call
    os.system("ffmpeg -i %s %s" % (clipFileName, mp4FileName))
    os.remove(clipFileName)
    conversionQueue.task_done()
    logging.debug(
        "Done mp4 conversion of file %s" % os.path.basename(clipFileName))


class VideoSplitterThread(object):
  """Class to draw split video into clips"""

  def __init__(self, configFileName, videoFileName, clipsOutputFolder):
    """Initialize values"""
    self.config = Config(configFileName)
    self.videoFileName = videoFileName
    self.clipsOutputFolder = clipsOutputFolder
    self.tempFolder = os.path.join(
        '/mnt/tmp', os.path.basename(videoFileName).split('.')[0])
    Config.mkdir_p(self.tempFolder)

    self.numFrameInClip = self.config.hdf5_clip_frame_count
    self.videoClipsMapFilename = os.path.join(
        self.clipsOutputFolder, self.config.hdf5_video_clips_map_filename)
    self.frameDensity = self.config.sw_frame_density

    Config.mkdir_p(self.clipsOutputFolder)

    # Logging levels
    logging.basicConfig(
        format=
        '{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s',
        level=self.config.lg_log_level,
        datefmt="%Y-%m-%d--%H:%M:%S")

  def run(self):
    """Split video into clips"""
    startTime = time.time()
    logging.info("Setting up split for video %s" % self.videoFileName)

    # keep track of frame numbers for each clip
    videoClipsMap = {}

    # conversion threads
    conversionQueue = JoinableQueue()
    conversionProcesses = []
    # num_consumers = 1
    num_consumers = max(int(
        self.config.multipleOfCPUCount * multiprocessing.cpu_count()), 1)

    for i in xrange(num_consumers):
      conversionProcess = Process(
          target=runAviToMp4Converter,
          args=(conversionQueue,))
      conversionProcesses += [conversionProcess]
      conversionProcess.start()

    videoFrameReader = VideoFrameReader(self.videoFileName)
    fps = videoFrameReader.getFPS()
    imageDim = videoFrameReader.getImageDim()

    # clip number
    clipId = 0
    clipWriter = None
    outClipFileName = None
    currentFrameNum = 0  # frame number being extracted

    frame = videoFrameReader.getFrameWithFrameNumber(
        int(self.config.ci_videoFrameNumberStart))
    while frame != None:
      if ((currentFrameNum % self.numFrameInClip) == 0):
        if clipWriter != None:
          # close clip and kick off mp4 conversion
          clipWriter.save()
          conversionQueue.put(outClipFileName)
          videoClipsMap[clipId]['frame_number_end'] = (currentFrameNum - 1)
          clipId += 1
        logging.debug("Creating new clip id: %d" % clipId)
        outClipFileName = os.path.join(
            self.clipsOutputFolder, "%d.avi" % clipId)
        clipWriter = VideoWriter(outClipFileName, fps, imageDim)
        videoClipsMap[clipId] = {
            'clip_filename': "%d.mp4" % clipId,
            'frame_number_start': currentFrameNum
        }

      logging.debug("Adding frame %d to video" % currentFrameNum)
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

    # close last clip writer
    if clipWriter != None:
      # close clip and kick off mp4 conversion
      clipWriter.save()
      conversionQueue.put(outClipFileName)
      videoClipsMap[clipId]['frame_number_end'] = (currentFrameNum - 1)

    # write map file
    with open(self.videoClipsMapFilename, "w") as f:
      json.dump(videoClipsMap, f, indent=2)

    # Close video reader
    videoFrameReader.close()

    # join conversion threads
    logging.info("Waiting for mp4 conversion threads to complete")
    for i in xrange(num_consumers):
      conversionQueue.put(None)
    conversionQueue.join()
    logging.debug("Mp4 conversion queues joined")
    for conversionProcess in conversionProcesses:
      conversionProcess.join()
    logging.debug("Mp4 conversion processes joined")

    # Exit
    logging.info("Finished creating clips")
    endTime = time.time()
    logging.info(
        'It took VideoSplitterThread %s seconds to complete' %
        (endTime - startTime))
