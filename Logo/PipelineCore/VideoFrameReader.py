import time

from VideoReader import VideoReader

from Logo.PipelineMath.Rectangle import Rectangle


class VideoFrameReader(object):
  """Wrapper around cpp VideoReader.VideoFrameReader class"""

  def __init__(self, videoFileName):
    """Initialization"""
    # Load video - since no expilicit synchronization exists to check if
    # VideoReader is ready, wait for 10 seconds
    self.videoFrameReader = VideoReader.VideoFrameReader(5000, 5000, videoFileName)
    self.videoFrameReader.generateFrames()
    time.sleep(1)

    # Get frame dimensions and create bounding boxes
    frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    while not frame:
      frame = self.videoFrameReader.getFrameWithFrameNumber(1)
    self.imageDim = Rectangle.rectangle_from_dimensions(
        frame.width, frame.height)
    self.fps = self.videoFrameReader.fps
    self.lengthInMicroSeconds = self.videoFrameReader.lengthInMicroSeconds
    self.currentFrameNum = 0

  def getLengthInMicroSeconds(self):
    """Get length of video"""
    return self.lengthInMicroSeconds

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
