import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle


class BoundingBoxes(object):
  """Create sliding window coordinates"""

  def __init__(self, imageWidth, imageHeight, 
      xstepSize, ystepSize, patchWidth, patchHeight, scales):
    """Initialize bounding box base sizes"""
    self.imageWidth = imageWidth
    self.imageHeight = imageHeight
    self.xstepSize = xstepSize
    self.ystepSize = ystepSize
    self.patchWidth = patchWidth
    self.patchHeight = patchHeight
    self.scales = scales

    self.imageDim = Rectangle.rectangle_from_dimensions(
        self.imageWidth, self.imageHeight)
    # cache static computations at various scales
    self.cachedBoundingBoxes = {}

  def getBoundingBoxes(self, scaleFactor):
    """Get different bounding boxes at given scaleFactor"""
    if scaleFactor in self.cachedBoundingBoxes.keys():
      return self.cachedBoundingBoxes[scaleFactor]
    boundingBoxes = []
    scaledImageDim = self.imageDim.get_scaled_rectangle(scaleFactor)
    width = scaledImageDim.width
    height = scaledImageDim.height
    x = 0
    while x + self.patchWidth <= width:
      y = 0
      while y + self.patchHeight <= height:
        boundingBoxes.append((x, y, self.patchWidth, self.patchHeight))
        y += self.ystepSize[scaleFactor]
      if y - self.ystepSize[scaleFactor] + self.patchHeight != height:
        boundingBoxes.append(
            (x, int(height - self.patchHeight), self.patchWidth,
             self.patchHeight))
      x += self.xstepSize[scaleFactor]

    if x - self.xstepSize[scaleFactor] + self.patchWidth != width:
      y = 0
      while y + self.patchHeight <= height:
        boundingBoxes.append(
            (int(width - self.patchWidth), y, self.patchWidth,
             self.patchHeight))
        y += self.ystepSize[scaleFactor]

    if x - self.xstepSize[scaleFactor] + self.patchWidth != width\
        and y - self.ystepSize[scaleFactor] + self.patchHeight != height:
      boundingBoxes.append((int(width - self.patchWidth),
                            int(height - self.patchHeight),
                            self.patchWidth, self.patchHeight))
    self.cachedBoundingBoxes[scaleFactor] = boundingBoxes
    return boundingBoxes

  def getNumOfSlidingWindows(self):
    """Get total number of sliding window patches"""
    numOfSlidingWindows = 0
    for scale in self.scales:
      numOfSlidingWindows += len(self.getBoundingBoxes(scale))
    return numOfSlidingWindows
