import subprocess
import time
import json

from VideoReader import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle


class VideoFrameReader(object):
  """Wrapper around cpp VideoReader.VideoFrameReader class"""

  def __init__(self, videoFileName):
    """Initialization"""
    self.videoFileName = videoFileName
    # Load video - since no expilicit synchronization exists to check if
    # VideoReader is ready, wait for 10 seconds
    self.videoFrameReader = VideoReader.VideoFrameReader(150, 150, videoFileName)
    self.videoFrameReader.generateFrames()
    time.sleep(10)

    # Get frame dimensions and create bounding boxes
    frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    while not frame:
      frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    self.imageDim = Rectangle.rectangle_from_dimensions(
        frame.width, frame.height)
    self.fps = self.videoFrameReader.fps
    self.currentFrameNum = 0

  def getLengthInMicroSeconds(self):
    """Get length of video"""
    return VideoFrameReader.getLengthInSeconds(self.videoFileName) * 1000000

  def getImageDim(self):
    """Get image dim"""
    return self.imageDim

  def getFPS(self):
    """Get FPS"""
    return self.fps

  def getFrameWithFrameNumber(self, frameNumber):
    """Get frame with specified number. If none exists, return None"""
    while (not self.videoFrameReader.eof) or (
        self.currentFrameNum <= self.videoFrameReader.totalFrames):
      frame = self.videoFrameReader.getFrameWithFrameNumber(
          int(self.currentFrameNum))
      while not frame:
        frame = self.videoFrameReader.getFrameWithFrameNumber(
            int(self.currentFrameNum))
      if frameNumber == self.currentFrameNum:
        return frame
      self.currentFrameNum += 1
    # if frame was not found, return None
    return None

  def savePngWithFrameNumber(self, frameNumber, imageFileName):
    """Save PNG with frame number"""
    if self.getFrameWithFrameNumber(frameNumber) == None:
      return False
    else:
      self.videoFrameReader.savePngWithFrameNumber(
          int(frameNumber), str(imageFileName))
      return True

  def close(self):
    """Gracefully close the stream"""
    # HACK: quit video reader gracefully
    self.currentFrameNum = self.videoFrameReader.totalFrames
    while (not self.videoFrameReader.eof) or (
        self.currentFrameNum <= self.videoFrameReader.totalFrames):
      self.videoFrameReader.seekToFrameWithFrameNumber(self.currentFrameNum)
      self.currentFrameNum += 1
    return True

  @staticmethod
  def getLengthInSeconds(videoFileName):
    """Run ffprobe and return video length"""
    ffprobeCmd = "ffprobe -v quiet -print_format json -show_format -show_streams %s" % videoFileName

    length = 0
    try:
      ffprobeResult = subprocess.Popen(ffprobeCmd, shell=True, stdout=subprocess.PIPE).stdout.read()
      ffprobeJSON = json.loads(ffprobeResult)

      # get length
      start_time = float(ffprobeJSON["format"]["start_time"])
      duration = float(ffprobeJSON["format"]["duration"])
      length = duration - start_time # get length in seconds

    except:
      print "Command: '%s'" % ffprobeCmd
      print "Could not run ffprobe in video file %s" % videoFileName

    return length
