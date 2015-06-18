import cv2
import cv2.cv as cv


class VideoWriter(object):
  """Create an AVI video by adding frames one by one"""

  def __init__(self, videoFileName, fps, imageDim):
    """Initialize writer"""
    fourcc = cv.CV_FOURCC('M', 'J', 'P', 'G')
    self.writer = cv2.VideoWriter(videoFileName, fourcc, fps,\
      (imageDim.width, imageDim.height))

  def addFrame(self, imageManipulator):
    """Add a manipulated image to writer"""
    self.writer.write(imageManipulator.getImage())

  def save(self):
    """Close write buffer and save the video"""
    cv2.destroyAllWindows()
    self.writer.release()
