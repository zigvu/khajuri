import math, os
import logging
import numpy as np
from shapely.geometry import box
from multiprocessing import Process, Manager
from Queue import Queue, Empty
import multiprocessing
import time, pickle

def setupNeighbor( neighbors, cellBoundaries, cb ):
  centralBox = box( cb[ 'x0' ] - 1, cb[ 'y0' ] - 1, cb[ 'x3' ] + 1, cb[ 'y3' ] + 1 )
  boxes = []
  for neighbor in cellBoundaries:
    if neighbor == cb:
      continue
    neighborBox = box( neighbor[ 'x0' ] - 1, neighbor[ 'y0' ] - 1,
        neighbor[ 'x3' ] + 1, neighbor[ 'y3' ] + 1 )
    if neighborBox.intersects( centralBox ):
      boxes.append( neighbor )
  neighbors[ ( cb[ 'x0' ], cb[ 'y0'], cb[ 'x3' ], cb[ 'y3' ], cb[ 'idx' ] ) ] = boxes

class PixelMap(object):
  def __init__(self, allCellBoundariesDict, scaleFactor):
    """Initialize pixelMap based on cell boundaries"""
    self.scaleFactor = scaleFactor
    self.allCellBoundariesDict = allCellBoundariesDict
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

  def copy(self):
    """Return a new copy of this map"""
    newPixelMap = PixelMap(self.allCellBoundariesDict, self.scaleFactor)
    newPixelMap.cellValues = self.cellValues.copy()
    return newPixelMap

  def toNumpyArray(self):
    """Converts this PixelMap to a numpy array"""
    start = time.time()
    pixelCount = np.zeros((self.height, self.width))
    for cb in self.cellBoundaries:
      pixelCount[cb["y0"]:cb["y3"], cb["x0"]:cb["x3"]] = self.cellValues[cb["idx"]]
    end = time.time()
    return pixelCount

  # ********************
  # Add scores from json

  def addScore(self, x0, y0, x3, y3, score):
    """Add scores to cells"""
    cells = self.cellSlidingWindows[ (x0, y0, x3, y3 ) ]
    self.cellValues[np.array( cells )] += score

  def addScore_average(self, x0, y0, x3, y3, score):
    """Average score with existing cell values"""
    cells = self.cellSlidingWindows[ (x0, y0, x3, y3 ) ]
    self.cellValues[np.array( cells )] += score
    self.cellValues[np.array( cells )] /= 2

  def addScore_max(self, x0, y0, x3, y3, score):
    """Store max of score and existing cell values in cells"""
    cells = self.cellSlidingWindows[ (x0, y0, x3, y3 ) ]
    myCells = self.cellValues[np.array( cells )]
    mask = myCells < score
    myCells[ mask ] = score
    self.cellValues[np.array( cells )] = myCells

  # ********************
  # Helper functions
  # ********************
  def setScale(self, scaleFactor):
    """Set scale of this PixelMap object"""
    self.cellBoundariesDict = self.allCellBoundariesDict['scales'][scaleFactor]
    self.cellBoundaries = self.cellBoundariesDict["cell_boundaries"]
    self.cellSlidingWindows = self.cellBoundariesDict["sw_mapping"]
    self.width = self.cellBoundariesDict["width"]
    self.height = self.cellBoundariesDict["height"]
    self.scaleFactor = scaleFactor

  # ********************
  # Static methods to create cell boundaries

  @staticmethod
  def getCellBoundaries(staticBoundingBoxes, scales):
    """Return cell boundaries for given scales.
    The data structure holding the cell boundaries is a dictionary with each scale factor
    as the key. For each scale, we get the frame width, height, number of cells, cell 
    boundaries bbox and mapping for each sliding window to cell boundaries using idx
    This method is compute heavy - it should be called once and its return value should be
    shared across processes.
    General idea: (a) Create cells for each scale by multiplying prime numbers for each sliding
    window. Then, resize all such cells to the smallest scale and combine with each other.
    The resulting cell boundaries are all unique "pixels" in our new PixelMap. However, to 
    account for fractional scales, (b) we need to split cells that lie on sliding window boundaries
    at each scale. (c) Finally, these cells are mapped to sliding windows at each scale. This mapping
    dictionary is returned.
    Returns mapping dictionary"""
    # Load existing one from File System if it exists
    saveFile = "/tmp/savedBoundaries.p"
    useSavedOne = False
    if os.path.exists( saveFile ):
      allCellBoundaries = pickle.load( open( saveFile, "rb" ) )
      if set( allCellBoundaries[ "scales" ].keys() ) == set(scales):
        useSavedOne = True
        for s in scales:
          existingXStride =  allCellBoundaries[ "scales" ][s] [ "xStride" ]
          existingYStride =  allCellBoundaries[ "scales" ][s] [ "yStride" ]
          newXStride  = staticBoundingBoxes.xstepSize[ s ]
          newYStride  = staticBoundingBoxes.ystepSize[ s ]
          if existingXStride != newXStride or existingYStride != newYStride:
            useSavedOne = False
        
      if allCellBoundaries[ "frameDim" ][ "width" ] != staticBoundingBoxes.imageDim.width:
        useSavedOne = False
      if allCellBoundaries[ "frameDim" ][ "height" ] != staticBoundingBoxes.imageDim.height:
        useSavedOne = False
    if useSavedOne:
      logging.info( "Using already computed boundaries from file at %s" % saveFile )
      return allCellBoundaries
    else:
      logging.info( "Calculating new cellMap and saving to file %s" % saveFile)


    # -------------------------------------------------------------
    # Part (a) : Create and combine cells at each scale
    # prime number generator for combination of cells across scales
    primesForCells = PixelMap.generatePrimes()
    # keep track of sliding window boundaries
    rAxisLines = []
    cAxisLines = []
    # get smallest scale pixel cells
    allScales = sorted(scales)
    smallestScale = min(allScales)
    smallestScaleRect = staticBoundingBoxes.imageDim.get_scaled_rectangle(smallestScale)
    smallestPixelCount = np.ones((smallestScaleRect.height, smallestScaleRect.width)) # row, column
    # for each scale, add in new cell information
    for scaleFactor in allScales:
      rect = staticBoundingBoxes.imageDim.get_scaled_rectangle(scaleFactor)
      slidingWindows = staticBoundingBoxes.getBoundingBoxes(scaleFactor)
      # for each sliding window, populate with multiples of primes
      pixelCount = np.ones((rect.height, rect.width)) # row, column
      primesForSlw = PixelMap.generatePrimes()
      for slw in slidingWindows:
        rStart = slw[1] ; rEnd = slw[1] + slw[3]
        cStart = slw[0] ; cEnd = slw[0] + slw[2]
        # keep track of unique patches by muliplying primes
        pixelCount[rStart:rEnd, cStart:cEnd] *= next(primesForSlw)
        # add axis lines - rescale to smallest scale factor
        rAxisLines += [int(rStart * smallestScale/scaleFactor), int(rEnd * smallestScale/scaleFactor)]
        cAxisLines += [int(cStart * smallestScale/scaleFactor), int(cEnd * smallestScale/scaleFactor)]
      # error check: ensure that all pixels got populated
      if np.min(pixelCount) <= 1:
        raise RuntimeError("Sliding window didn't cover some pixels")
      # now, zoom to be as large as smallestPixelCount
      pixelCountZoomed = PixelMap.simpleZoom(pixelCount, smallestScaleRect.width, smallestScaleRect.height)
      # create cell boundaries - unique value in pixelCountZoomed delineate cells
      boundaryPixelCount = np.zeros(np.shape(smallestPixelCount))
      uniqueValues = np.unique(pixelCountZoomed)
      for uniqueValue in uniqueValues:
        cb = np.where(pixelCountZoomed == uniqueValue)
        rBegin = np.min(cb[0]) ; rEnd = np.max(cb[0]) + 1
        cBegin = np.min(cb[1]) ; cEnd = np.max(cb[1]) + 1
        #print "{x0: %d, y0: %d, x3: %d, y3: %d}" % (cBegin, rBegin, cEnd, rEnd)  # For testing
        boundaryPixelCount[rBegin:rEnd, cBegin:cEnd] = next(primesForCells)
      # error check: ensure that all pixels got populated
      if np.min(boundaryPixelCount) <= 1:
        raise RuntimeError("Sliding window for boundaryPixelCount didn't cover some pixels")
      # combine with all the rest boundaries from other scales
      smallestPixelCount *= boundaryPixelCount
    # error check: ensure that all pixels got populated
    if np.min(smallestPixelCount) <= 1:
      raise RuntimeError("Sliding window for smallestPixelCount didn't cover some pixels")

    # -------------------------------------------------------------
    # Part (b) : Divide cells which are dissected by sliding window boundaries
    # relabel first - start with new primes
    #print 'Unique before relabel: %s' % len(np.unique(smallestPixelCount))
    counter = 0 
    primesForCells = PixelMap.generatePrimes()
    uniqueValues = np.unique(smallestPixelCount)
    relabelPixelCount = np.zeros(np.shape(smallestPixelCount))
    for uniqueValue in uniqueValues:
      cb = np.where(smallestPixelCount == uniqueValue)
      rBegin = np.min(cb[0]) ; rEnd = np.max(cb[0]) + 1
      cBegin = np.min(cb[1]) ; cEnd = np.max(cb[1]) + 1
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
          rBegin = np.min(cb[0]) ; rEnd = np.max(cb[0]) + 1
          cBegin = np.min(cb[1]) ; cEnd = np.max(cb[1]) + 1
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
          rBegin = np.min(cb[0]) ; rEnd = np.max(cb[0]) + 1
          cBegin = np.min(cb[1]) ; cEnd = np.max(cb[1]) + 1
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
    allCellBoundaries = {"scales": {}, "frameDim" : {} }
    allCellBoundaries[ "frameDim" ] [ "width" ] = staticBoundingBoxes.imageDim.width
    allCellBoundaries[ "frameDim" ] [ "height" ] = staticBoundingBoxes.imageDim.height
    for scaleFactor in allScales:
      cellBoundaries = []
      cellCounter = 0
      slidingWindows = staticBoundingBoxes.getBoundingBoxes(scaleFactor)
      rect = staticBoundingBoxes.imageDim.get_scaled_rectangle(scaleFactor)
      # zoom up from smallest scale to current scale
      pixelCountZoomed = PixelMap.simpleZoom(finalPixelCount, rect.width, rect.height)
      uniqueValues = np.unique(pixelCountZoomed)
      testPixelCount = np.zeros(np.shape(pixelCountZoomed))
      # create data cell boundaries
      for uniqueValue in uniqueValues:
        cb = np.where(pixelCountZoomed == uniqueValue)
        rBegin = np.min(cb[0]) ; rEnd = np.max(cb[0]) + 1
        cBegin = np.min(cb[1]) ; cEnd = np.max(cb[1]) + 1
        #print "{x0: %d, y0: %d, x3: %d, y3: %d}" % (cBegin, rBegin, cEnd, rEnd) # For testing
        testPixelCount[rBegin:rEnd, cBegin:cEnd] += 1
        cellBoundaries += [{"x0": cBegin, "y0": rBegin, "x3": cEnd, "y3": rEnd, "idx": cellCounter}]
        cellCounter += 1
      # error check: ensure that all pixels got visited once and no pixel got visited twice
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
        rStart = slw[1] ; rEnd = slw[1] + slw[3]
        cStart = slw[0] ; cEnd = slw[0] + slw[2]
        # collect all cell counters for this sliding window
        cellIdxs = []
        for cb in cellBoundaries:
          # if the origin of cb is in this sliding window, collect it in
          if ((cb["x0"] >= cStart) and (cb["x0"] < cEnd) and (cb["y0"] >= rStart) and (cb["y0"] < rEnd)):
            cellIdxs += [cb["idx"]]
        cellSlidingWindows[ ( cStart, rStart, cEnd, rEnd ) ] = cellIdxs
      #neighbors = PixelMap.setupNeighbors( cellBoundaries )
      neighbors = []
      # save data to dictionary
      allCellBoundaries["scales"][scaleFactor] = {\
        "cell_boundaries": cellBoundaries, \
        "sw_mapping": cellSlidingWindows, \
        "max_cell_counter": (cellCounter - 1), \
        "width": rect.width, "height": rect.height, \
        "neighbors" : neighbors,\
        "xStride"  : staticBoundingBoxes.xstepSize [ scaleFactor ],
        "yStride"  : staticBoundingBoxes.ystepSize [ scaleFactor ]}
      # print progress
      #print "Scale %0.2f, unique: %d" % (scaleFactor, len(uniqueValues))
      logging.info("Finished working on scale %.2f. Unique values: %d" % (scaleFactor, len(uniqueValues)))

    # error check: we shouldn't have different max_cell_counter
    maxCellCounter = allCellBoundaries["scales"][smallestScale]["max_cell_counter"]
    for scaleFactor in allCellBoundaries["scales"]:
      if allCellBoundaries["scales"][scaleFactor]["max_cell_counter"] != maxCellCounter:
        raise RuntimeError("Cell boundaries across scales are different")

    pickle.dump( allCellBoundaries, open( saveFile, "wb" ) )
    return allCellBoundaries

  @staticmethod
  def setupNeighbors( cellBoundaries ):
    activeProcess = Queue()
    manager = Manager()
    neighbors = manager.dict()
    for cb in cellBoundaries:
      while len( multiprocessing.active_children()) >= multiprocessing.cpu_count():
        try:
          for i in range( multiprocessing.cpu_count() / 3 ):
              q = activeProcess.get(False)
              if q:
                q.join()
        except Empty:
          break
      p = Process( target=setupNeighbor, args=( neighbors, cellBoundaries, cb ) )
      p.start()
      activeProcess.put( p )
    while activeProcess.qsize() > 0:
      try:
         q = activeProcess.get(False)
         if q:
           q.join()
      except Empty:
        break
    return neighbors.copy()


  @staticmethod
  def generatePrimes():
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

  @staticmethod
  def simpleZoom(inputArray, newWidth, newHeight):
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
        scaledArray[y,x] = inputArray[int(scaleY * y), int(scaleX * x)]
    if np.min(scaledArray) < 0:
      raise RuntimeError("Not all values could be populated during zoom")
    return scaledArray
