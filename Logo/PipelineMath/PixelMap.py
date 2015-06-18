import os
import logging
import numpy as np
from shapely.geometry import box
from multiprocessing import Process, Manager
from threading import Thread
from Queue import Queue, Empty
import multiprocessing
import time
import cPickle as pickle


class PixelMap(object):
  """Container data structure for creating/hodling caffe scores"""

  def __init__(self, allCellBoundariesDict, neighborMap, scaleFactor):
    """Initialize pixelMap based on cell boundaries"""
    self.scaleFactor = scaleFactor
    self.allCellBoundariesDict = allCellBoundariesDict
    self.neighborMap = neighborMap
    self.setScale(self.scaleFactor)
    self.cellValues = np.zeros(self.cellBoundariesDict["max_cell_counter"] + 1)

  # ********************
  # Overloaded operators

  def __add__(self, anotherPixelMap):
    """Adds anotherPixelMap to current pixelMap and returns self"""
    self.cellValues += anotherPixelMap.cellValues
    return self

  def __sub__(self, anotherPixelMap):
    """Subtracts anotherPixelMap from current pixelMap and returns self"""
    self.cellValues -= anotherPixelMap.cellValues
    return self

  def __mul__(self, anotherPixelMap):
    """Multiply anotherPixelMap to current pixelMap and returns self"""
    self.cellValues *= anotherPixelMap.cellValues
    return self

  def __div__(self, anotherPixelMap):
    """Divides anotherPixelMap from current pixelMap and returns self"""
    if 0 in np.unique(anotherPixelMap.cellValues):
      raise RuntimeError("Division by zero in PixelMap")
    self.cellValues /= anotherPixelMap.cellValues
    return self

  # ********************
  # Utility functions

  def resize(self, newScale):
    """Resizes the current PixelMap and returns self"""
    self.setScale(newScale)
    return self

  ##@profile
  def copy(self):
    """Return a new copy of this map"""
    newPixelMap = PixelMap(
        self.allCellBoundariesDict, self.neighborMap, self.scaleFactor)
    newPixelMap.cellValues = self.cellValues.copy()
    return newPixelMap

  def toNumpyArray(self):
    """Converts this PixelMap to a numpy array"""
    pixelCount = np.zeros((self.height, self.width))
    for idx, cb in self.cellBoundaries.iteritems():
      pixelCount[cb["y0"]:cb["y3"], cb["x0"]:cb["x3"]] = self.cellValues[idx]
    return pixelCount

  def BFS(self, index):
    cb = self.cellBoundaries[index]
    xMin = cb["x0"]
    yMin = cb["y0"]
    xMax = cb["x3"]
    yMax = cb["y3"]
    neighbors = set()
    unvisitedCells = set()
    unvisitedCells.add(index)
    while len(unvisitedCells) > 0:
      index = unvisitedCells.pop()
      if index in neighbors:
        continue
      for n in self.neighborMap[self.scaleFactor][index].keys():
        if n not in neighbors and self.cellValues[n] > 0:
          cb = self.neighborMap[self.scaleFactor][index][n]
          if xMin > cb[0]:
            xMin = cb[0]
          if yMin > cb[1]:
            yMin = cb[1]
          if xMax < cb[2]:
            xMax = cb[2]
          if yMax < cb[3]:
            yMax = cb[3]
          unvisitedCells.add(n)
      neighbors.add(index)
    maxValue = np.max(self.cellValues[list(neighbors)])
    sumValue = 0
    areaTotal = 0
    for n in neighbors:
      sumValue += (self.cellValues[n] * self.cellAreas[n])
      areaTotal += self.cellAreas[n]
    avgValue = sumValue / (1.0 * areaTotal)
    return neighbors, maxValue, avgValue, (xMin, yMin, xMax, yMax)

  # ********************
  # convert from frame.scores to cellValues
  # ********************
  #@profile
  def addScore(self, patchScores):
    """Add scores to cells"""
    patchMapping = self.allCellBoundariesDict["patchMapping"]
    patchIdToBbox = {v: k for k, v in patchMapping.items()}
    aboveZeroPatchIds = np.argwhere(patchScores > 0)
    if len(aboveZeroPatchIds):
      for patchId in aboveZeroPatchIds:
        patchBbox = patchIdToBbox[patchId[0]]
        if self.scaleFactor == patchBbox[0]:
          cells = self.cellSlidingWindows[
              (patchBbox[1], patchBbox[2], patchBbox[3], patchBbox[4])
          ]
          self.cellValues[cells] += patchScores[patchId[0]]

  #@profile
  def addScore_max(self, patchScores):
    """Store max of score and existing cell values in cells"""
    patchMapping = self.allCellBoundariesDict["patchMapping"]
    patchIdToBbox = {v: k for k, v in patchMapping.items()}
    aboveZeroPatchIds = np.argwhere(patchScores > 0)
    if len(aboveZeroPatchIds):
      for patchId in aboveZeroPatchIds:
        patchBbox = patchIdToBbox[patchId[0]]
        if self.scaleFactor == patchBbox[0]:
          cells = self.cellSlidingWindows[
              (patchBbox[1], patchBbox[2], patchBbox[3], patchBbox[4])
          ]
          score = patchScores[patchId[0]]
          myCells = self.cellValues[np.array(cells)]
          mask = myCells < score
          myCells[mask] = score
          self.cellValues[np.array(cells)] = myCells

  # ********************
  # Helper functions
  # ********************
  def setScale(self, scaleFactor):
    """Set scale of this PixelMap object"""
    self.cellBoundariesDict = self.allCellBoundariesDict['scales'][scaleFactor]
    self.cellBoundaries = self.cellBoundariesDict["cell_boundaries"]
    self.cellAreas = self.cellBoundariesDict["cell_areas"]
    self.cellSlidingWindows = self.cellBoundariesDict["sw_mapping"]
    self.width = self.cellBoundariesDict["width"]
    self.height = self.cellBoundariesDict["height"]
    self.scaleFactor = scaleFactor


from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.Rectangle import Rectangle


class CellBoundaries(object):

  def __init__(self, config):
    self.config = config
    imgDim = Rectangle.rectangle_from_dimensions(
        self.config.sw_frame_width, self.config.sw_frame_height)
    patchDim = Rectangle.rectangle_from_dimensions(
        self.config.sw_patchWidth, self.config.sw_patchHeight)
    staticBBoxes = BoundingBoxes(
        imgDim, self.config.sw_xStride, self.config.sw_yStride, patchDim)
    self.allCellBoundariesDict = self.getCellBoundaries(
        staticBBoxes, self.config.sw_scales)

  def getCellBoundaries(self, staticBBoxes, scales):
    """Return cell boundaries for given scales.
    The data structure holding the cell boundaries is a dictionary with each 
    scale factor as the key. For each scale, we get the frame width, height, 
    number of cells, cell boundaries bbox and mapping for each sliding window 
    to cell boundaries using idx.
    This method is compute heavy - it should be called once and its return 
    value should be shared across processes.
    General idea: 
    (a) Create cells for each scale by multiplying prime numbers for each 
    sliding window. Then, resize all such cells to the smallest scale and 
    combine with each other. The resulting cell boundaries are all unique 
    "pixels" in our new PixelMap. However, to account for fractional scales, 
    (b) we need to split cells that lie on sliding window boundaries at each 
    scale. 
    (c) Finally, these cells are mapped to sliding windows at each scale. This 
    mapping dictionary is returned.
    
    Returns mapping dictionary
    """
    # Load existing one from File System if it exists
    saveFile = "/tmp/savedBoundaries.p"
    useSavedOne = False
    if os.path.exists(saveFile):
      allCellBoundaries = pickle.load(open(saveFile, "rb"))
      if set(allCellBoundaries["scales"].keys()) == set(scales):
        useSavedOne = True
        for s in scales:
          existingXStride = allCellBoundaries["scales"][s]["xStride"]
          existingYStride = allCellBoundaries["scales"][s]["yStride"]
          newXStride = staticBBoxes.xstepSize[s]
          newYStride = staticBBoxes.ystepSize[s]
          if existingXStride != newXStride or existingYStride != newYStride:
            useSavedOne = False

      if allCellBoundaries["frameDim"]["width"] != staticBBoxes.imageDim.width:
        useSavedOne = False
      if allCellBoundaries["frameDim"]["height"
                                      ] != staticBBoxes.imageDim.height:
        useSavedOne = False

    if useSavedOne:
      logging.info(
          "Using already computed boundaries from file at %s" % saveFile)
      return allCellBoundaries
    else:
      logging.info("Calculating new cellMap and saving to file %s" % saveFile)
      os.remove("/tmp/savedBoundaries.p")
      os.remove("/tmp/savedNeighbors.p")

    # -------------------------------------------------------------
    # Part (a) : Create and combine cells at each scale
    # prime number generator for combination of cells across scales
    primesForCells = self.generatePrimes()
    # keep track of sliding window boundaries
    rAxisLines = []
    cAxisLines = []
    # get smallest scale pixel cells
    allScales = sorted(scales)
    smallestScale = min(allScales)
    smallestScaleRect = staticBBoxes.imageDim.get_scaled_rectangle(
        smallestScale)
    smallestPixelCount = np.ones(
        (smallestScaleRect.height, smallestScaleRect.width)
    )  # row, column
    # for each scale, add in new cell information
    patchMapping = {}
    patchId = 0
    for scale in scales:
      for c in staticBBoxes.getBoundingBoxes(scale):
        rStart = c[1]
        rEnd = c[1] + c[3]
        cStart = c[0]
        cEnd = c[0] + c[2]
        patchMapping[(scale, cStart, rStart, cEnd, rEnd)] = patchId
        patchId += 1

    for scaleFactor in allScales:
      rect = staticBBoxes.imageDim.get_scaled_rectangle(scaleFactor)
      slidingWindows = staticBBoxes.getBoundingBoxes(scaleFactor)
      # for each sliding window, populate with multiples of primes
      pixelCount = np.ones((rect.height, rect.width))  # row, column
      primesForSlw = self.generatePrimes()
      for slw in slidingWindows:
        rStart = slw[1]
        rEnd = slw[1] + slw[3]
        cStart = slw[0]
        cEnd = slw[0] + slw[2]
        # keep track of unique patches by muliplying primes
        pixelCount[rStart:rEnd, cStart:cEnd] *= next(primesForSlw)
        # add axis lines - rescale to smallest scale factor
        rAxisLines += [int(rStart * smallestScale / scaleFactor),
                       int(rEnd * smallestScale / scaleFactor)]
        cAxisLines += [int(cStart * smallestScale / scaleFactor),
                       int(cEnd * smallestScale / scaleFactor)]
      # error check: ensure that all pixels got populated
      if np.min(pixelCount) <= 1:
        raise RuntimeError("Sliding window didn't cover some pixels")
      # now, zoom to be as large as smallestPixelCount
      pixelCountZoomed = self.simpleZoom(
          pixelCount, smallestScaleRect.width, smallestScaleRect.height)
      # create cell boundaries - unique value in pixelCountZoomed delineate cells
      boundaryPixelCount = np.zeros(np.shape(smallestPixelCount))
      uniqueValues = np.unique(pixelCountZoomed)
      for uniqueValue in uniqueValues:
        cb = np.where(pixelCountZoomed == uniqueValue)
        rBegin = np.min(cb[0])
        rEnd = np.max(cb[0]) + 1
        cBegin = np.min(cb[1])
        cEnd = np.max(cb[1]) + 1
        #print "{x0: %d, y0: %d, x3: %d, y3: %d}" % (cBegin, rBegin, cEnd, rEnd)  # For testing
        boundaryPixelCount[rBegin:rEnd, cBegin:cEnd] = next(primesForCells)
      # error check: ensure that all pixels got populated
      if np.min(boundaryPixelCount) <= 1:
        raise RuntimeError(
            "Sliding window for boundaryPixelCount didn't cover some pixels")
      # combine with all the rest boundaries from other scales
      smallestPixelCount *= boundaryPixelCount
    # error check: ensure that all pixels got populated
    if np.min(smallestPixelCount) <= 1:
      raise RuntimeError(
          "Sliding window for smallestPixelCount didn't cover some pixels")

    # -------------------------------------------------------------
    # Part (b) : Divide cells which are dissected by sliding window boundaries
    # relabel first - start with new primes
    #print 'Unique before relabel: %s' % len(np.unique(smallestPixelCount))
    counter = 0
    primesForCells = self.generatePrimes()
    uniqueValues = np.unique(smallestPixelCount)
    relabelPixelCount = np.zeros(np.shape(smallestPixelCount))
    for uniqueValue in uniqueValues:
      cb = np.where(smallestPixelCount == uniqueValue)
      rBegin = np.min(cb[0])
      rEnd = np.max(cb[0]) + 1
      cBegin = np.min(cb[1])
      cEnd = np.max(cb[1]) + 1
      relabelPixelCount[rBegin:rEnd, cBegin:cEnd] = counter
      counter += 10

    #print 'Unique after relabel: %s' % len(np.unique(relabelPixelCount))
    # for each axis, dissect cells in boundaries
    rAxisLines = np.unique(rAxisLines)
    for rLine in rAxisLines:
      if (rLine > 0) and (rLine < smallestScaleRect.height):
        uniqueValues = np.unique(relabelPixelCount[rLine, :])
        for uniqueValue in uniqueValues:
          cb = np.where(relabelPixelCount == uniqueValue)
          rBegin = np.min(cb[0])
          rEnd = np.max(cb[0]) + 1
          cBegin = np.min(cb[1])
          cEnd = np.max(cb[1]) + 1
          relabelPixelCount[rBegin:rLine, cBegin:cEnd] = counter
          counter += 10
          relabelPixelCount[rLine:rEnd, cBegin:cEnd] = counter
          counter += 10
    cAxisLines = np.unique(cAxisLines)
    for cLine in cAxisLines:
      if (cLine > 0) and (cLine < smallestScaleRect.width):
        uniqueValues = np.unique(relabelPixelCount[:, cLine])
        for uniqueValue in uniqueValues:
          cb = np.where(relabelPixelCount == uniqueValue)
          rBegin = np.min(cb[0])
          rEnd = np.max(cb[0]) + 1
          cBegin = np.min(cb[1])
          cEnd = np.max(cb[1]) + 1
          relabelPixelCount[rBegin:rEnd, cBegin:cLine] = counter
          counter += 10
          relabelPixelCount[rBegin:rEnd, cLine:cEnd] = counter
          counter += 10

    finalPixelCount = relabelPixelCount
    # DEBUG : START : comment when not in debug mode
    # labelSmallestPixelCount = 1.0
    # relabelIncr = 0.000001 # allow for 1M unique values
    # labelCounter = 0
    # for r in np.arange(0, np.shape(finalPixelCount)[0]):
    #   for c in np.arange(0, np.shape(finalPixelCount)[1]):
    #     if finalPixelCount[r, c] > 1:
    #       finalPixelCount[finalPixelCount == finalPixelCount[r, c]] = \
    #         labelSmallestPixelCount - labelCounter * relabelIncr
    #       labelCounter += 1
    # if (np.min(finalPixelCount) <= 0) or (np.max(finalPixelCount) > 1):
    #   raise RuntimeError("Labeling of finalPixelCount resuled in error")
    # DEBUG : END : comment when not in debug mode

    # -------------------------------------------------------------
    # Part (c) : Create dictionary with data cell boundaries in each scale
    allCellBoundaries = {"scales": {}, "frameDim": {}}
    allCellBoundaries["frameDim"]["width"] = staticBBoxes.imageDim.width
    allCellBoundaries["frameDim"]["height"] = staticBBoxes.imageDim.height
    for scaleFactor in allScales:
      cellBoundaries = {}
      cellAreas = {}
      cellCounter = 0
      slidingWindows = staticBBoxes.getBoundingBoxes(scaleFactor)
      rect = staticBBoxes.imageDim.get_scaled_rectangle(scaleFactor)
      # zoom up from smallest scale to current scale
      pixelCountZoomed = self.simpleZoom(finalPixelCount, rect.width,
                                         rect.height)
      uniqueValues = np.unique(pixelCountZoomed)
      testPixelCount = np.zeros(np.shape(pixelCountZoomed))
      # create data cell boundaries
      for uniqueValue in uniqueValues:
        cb = np.where(pixelCountZoomed == uniqueValue)
        rBegin = np.min(cb[0])
        rEnd = np.max(cb[0]) + 1
        cBegin = np.min(cb[1])
        cEnd = np.max(cb[1]) + 1
        # For testing
        # print "{x0: %d, y0: %d, x3: %d, y3: %d}" % (cBegin, rBegin, cEnd, rEnd)
        testPixelCount[rBegin:rEnd, cBegin:cEnd] += 1
        cellBoundaries[cellCounter] = {
            "x0": cBegin,
            "y0": rBegin,
            "x3": cEnd,
            "y3": rEnd
        }
        cellAreas[cellCounter] = 1.0 * (cEnd - cBegin) * (rEnd - rBegin)
        cellCounter += 1
      # error check:
      # ensure that all pixels got visited once and no pixel got visited twice
      if (np.max(testPixelCount) > 1) or (np.min(testPixelCount) < 1):
        raise RuntimeError("Sliding window for testPixelCount not correct")

      # DEBUG : START : comment when not in debug mode
      # if scaleFactor == allScales[4]:
      #   return testPixelCount
      # continue
      # DEBUG : END : comment when not in debug mode

      # map cell counter idx to original sliding windows
      cellSlidingWindows = {}
      for slw in slidingWindows:
        rStart = slw[1]
        rEnd = slw[1] + slw[3]
        cStart = slw[0]
        cEnd = slw[0] + slw[2]
        # collect all cell counters for this sliding window
        cellIdxs = []
        for idx, cb in cellBoundaries.iteritems():
          # if the origin of cb is in this sliding window, collect it in
          if ((cb["x0"] >= cStart) and (cb["x0"] < cEnd) and
              (cb["y0"] >= rStart) and (cb["y0"] < rEnd)):
            cellIdxs += [idx]
        cellSlidingWindows[(cStart, rStart, cEnd, rEnd)] = cellIdxs
      # save data to dictionary
      allCellBoundaries["scales"][scaleFactor] = {\
        "cell_boundaries": cellBoundaries, \
        "cell_areas": cellAreas, \
        "sw_mapping": cellSlidingWindows, \
        "max_cell_counter": (cellCounter - 1), \
        "width": rect.width, "height": rect.height, \
        "xStride": staticBBoxes.xstepSize[scaleFactor], \
        "yStride": staticBBoxes.ystepSize[scaleFactor]}
      # print progress
      #print "Scale %0.2f, unique: %d" % (scaleFactor, len(uniqueValues))
      logging.info("Finished working on scale %.2f. Unique values: %d" %
                   (scaleFactor, len(uniqueValues)))

    # error check: we shouldn't have different max_cell_counter
    maxCellCounter = allCellBoundaries["scales"][smallestScale][
        "max_cell_counter"
    ]
    for scaleFactor in allCellBoundaries["scales"]:
      if allCellBoundaries["scales"][scaleFactor]["max_cell_counter"
                                                 ] != maxCellCounter:
        raise RuntimeError("Cell boundaries across scales are different")

    allCellBoundaries["patchMapping"] = patchMapping
    pickle.dump(allCellBoundaries, open(saveFile, "wb"))
    return allCellBoundaries

  def generatePrimes(self):
    """Generator for prime numbers"""
    D = {}
    q = 2  # first integer to test for primality.
    while True:
      if q not in D:
        # not marked composite, must be prime
        yield q
        #first multiple of q not already marked
        D[q * q] = [q]
      else:
        for p in D[q]:
          D.setdefault(p + q, []).append(p)
        # no longer need D[q], free memory
        del D[q]
      q += 1

  def simpleZoom(self, inputArray, newWidth, newHeight):
    """Scipy zoom replacement - doesn't introduce new values after resize.
    inputArray: numpy array
    newWidth: int
    newHeight: int
    Returns a zoomed up/down array"""
    inputHeight = np.shape(inputArray)[0]
    inputWidth = np.shape(inputArray)[1]
    if (inputHeight == newHeight) and (inputWidth == newWidth):
      return inputArray.copy()
    scaleY = 1.0 * inputHeight / newHeight
    scaleX = 1.0 * inputWidth / newWidth
    scaledArray = np.ones((newHeight, newWidth)) * -1
    # inefficient but gets the job done:
    for y in range(0, newHeight):
      for x in range(0, newWidth):
        scaledArray[y, x] = inputArray[int(scaleY * y), int(scaleX * x)]
    if np.min(scaledArray) < 0:
      raise RuntimeError("Not all values could be populated during zoom")
    return scaledArray


class NeighborsCache(object):

  def __init__(self, config):
    self.config = config
    self.neighborMap = None
    self.saveFile = "/tmp/savedNeighbors.p"
    self.loadFromCache()

  def neighborMapAllScales(self, cellBoundariesDict):
    if not self.neighborMap:
      self.neighborMap = {}
      for scale in cellBoundariesDict["scales"].keys():
        atScale = self.calculateNeighborMap(
            cellBoundariesDict["scales"][scale]["cell_boundaries"])
        self.neighborMap[scale] = atScale
      self.saveCache()
    return self.neighborMap

  def saveCache(self):
    pickle.dump(self.neighborMap, open(self.saveFile, "wb"))

  def loadFromCache(self):
    if os.path.exists(self.saveFile):
      self.neighborMap = pickle.load(open(self.saveFile, "rb"))

  def calculateNeighborMap(self, cellBoundaries):
    activeProcess = Queue()
    manager = Manager()
    neighbors = manager.dict()
    queueOfCBs = multiprocessing.Queue()
    for cb in cellBoundaries.iteritems():
      queueOfCBs.put(cb)

    for _i in range(multiprocessing.cpu_count()):
      queueOfCBs.put((0, None))
      p = Process(target=setupNeighbor,
                  args=(
                      queueOfCBs, neighbors, cellBoundaries))
      p.start()
      activeProcess.put(p)
    while activeProcess.qsize() > 0:
      try:
        q = activeProcess.get(False)
        if q:
          q.join()
      except Empty:
        break
    return neighbors.copy()


def setupNeighbor(queue, neighbors, cellBoundaries):
  while True:
    index, cb = queue.get()
    logging.info('Got cb : %s at index %s for setting up from queue' %
                 (cb, index))
    if not cb:
      break
    else:
      centralBox = box(cb['x0'] - 1, cb['y0'] - 1, cb['x3'] + 1, cb['y3'] + 1)
      boxes = {}
      for idx, neighbor in cellBoundaries.iteritems():
        if neighbor == cb:
          continue
        neighborBox = box(neighbor['x0'] - 1, neighbor['y0'] - 1,
                          neighbor['x3'] + 1, neighbor['y3'] + 1)
        if neighborBox.intersects(centralBox):
          boxes[idx] = (
              neighbor['x0'], neighbor['y0'], neighbor['x3'], neighbor['y3'],
          )
      neighbors[index] = boxes
