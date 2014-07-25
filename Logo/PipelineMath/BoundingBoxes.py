import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle

class BoundingBoxes( object ):
  def __init__( self, imageDim, xstepSize, ystepSize, patchDim ):
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

  def getBoundingBoxes( self, scaleFactor ):
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
        boundingBoxes.append( ( x, y, self.patchSizeWidth, self.patchSizeHeight ) )
        y += self.ystepSize
      if y - self.ystepSize + self.patchSizeHeight != height:
        boundingBoxes.append(( x, int( height - self.patchSizeHeight), self.patchSizeWidth, self.patchSizeHeight ) )
      x += self.xstepSize

    if x - self.xstepSize + self.patchSizeWidth != width:
      y = 0
      while y + self.patchSizeHeight <= height:
        boundingBoxes.append( ( int( width - self.patchSizeWidth ), y, self.patchSizeWidth, self.patchSizeHeight ) )
        y += self.ystepSize

    if x - self.xstepSize + self.patchSizeWidth != width\
        and y - self.ystepSize + self.patchSizeHeight != height:
      boundingBoxes.append( ( int( width - self.patchSizeWidth ), 
                              int( height - self.patchSizeHeight ), 
                              self.patchSizeWidth, self.patchSizeHeight ) )
    self.cachedBoundingBoxes[scaleFactor] = boundingBoxes
    return boundingBoxes

  def pixelMapToRemoveDoubleCounting(self, scaleFactor):
    """Get pixel count as window is slid over the image
    Remove double counting artifacts but no guarantees on border/corner cases
    Return pixelMap with per-pixel weights to rescale detection scores"""
    if scaleFactor in self.cachedPixelMaps.keys():
      return self.cachedPixelMaps[scaleFactor]
    scaledImageDim = self.imageDim.get_scaled_rectangle(scaleFactor)
    width = scaledImageDim.width
    height = scaledImageDim.height
    slidingWindows = self.getBoundingBoxes(scaleFactor)
    # row, column
    pixelCount = np.zeros((height, width))
    for slw in slidingWindows:
      rStart = slw[1]
      rEnd = slw[1] + slw[3]
      cStart = slw[0]
      cEnd = slw[0] + slw[3]
      #print "(" + str(slw[0]) + "," + str(slw[1]) + " : " + str(slw[2]) + "," + str(slw[3]) + ")"  
      pixelCount[rStart:rEnd, cStart:cEnd] += 1
    if pixelCount.min() <= 0:
      raise RuntimeError("PixelMap: Some pixels were not mapped at given scale")
    # remove all values except the two highest ones
    uniqueValues = np.unique(pixelCount)
    if len(uniqueValues) > 2:
      scoreMask = pixelCount < uniqueValues[-2]
      pixelCount[scoreMask] = uniqueValues[-2]
    scaleInverse = np.ones((height, width))
    pixelMap = scaleInverse / pixelCount
    self.cachedPixelMaps[scaleFactor] = pixelMap
    return pixelMap

