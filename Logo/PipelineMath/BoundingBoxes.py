import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle


class BoundingBoxes(object):
  """Create sliding window coordinates"""

  def __init__(self, imageDim, xstepSize, ystepSize, patchDim):
    """Initialize bounding box base sizes"""
    self.imageDim = imageDim
    self.imageWidth = imageDim.width
    self.imageHeight = imageDim.height
    self.xstepSize = xstepSize
    self.ystepSize = ystepSize
    self.patchSizeWidth = patchDim.width
    self.patchSizeHeight = patchDim.height
    # cache static computations at various scales
    self.cachedBoundingBoxes = {}
    self.cachedPixelMaps = {}

  def getBoundingBoxes(self, scaleFactor):
    """Get different bounding boxes at given scaleFactor"""
    if scaleFactor in self.cachedBoundingBoxes.keys():
      return self.cachedBoundingBoxes[scaleFactor]
    boundingBoxes = []
    scaledImageDim = self.imageDim.get_scaled_rectangle(scaleFactor)
    width = scaledImageDim.width
    height = scaledImageDim.height
    x = 0
    while x + self.patchSizeWidth <= width:
      y = 0
      while y + self.patchSizeHeight <= height:
        boundingBoxes.append((x, y, self.patchSizeWidth, self.patchSizeHeight))
        y += self.ystepSize[scaleFactor]
      if y - self.ystepSize[scaleFactor] + self.patchSizeHeight != height:
        boundingBoxes.append(
            (x, int(height - self.patchSizeHeight), self.patchSizeWidth,
             self.patchSizeHeight))
      x += self.xstepSize[scaleFactor]

    if x - self.xstepSize[scaleFactor] + self.patchSizeWidth != width:
      y = 0
      while y + self.patchSizeHeight <= height:
        boundingBoxes.append(
            (int(width - self.patchSizeWidth), y, self.patchSizeWidth,
             self.patchSizeHeight))
        y += self.ystepSize[scaleFactor]

    if x - self.xstepSize[scaleFactor] + self.patchSizeWidth != width\
        and y - self.ystepSize[scaleFactor] + self.patchSizeHeight != height:
      boundingBoxes.append((int(width - self.patchSizeWidth),
                            int(height - self.patchSizeHeight),
                            self.patchSizeWidth, self.patchSizeHeight))
    self.cachedBoundingBoxes[scaleFactor] = boundingBoxes
    return boundingBoxes
