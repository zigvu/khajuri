import numpy as np
import scipy.ndimage as ndimage
import Queue

from Logo.PipelineMath.Rectangle import Rectangle

class PeaksExtractor(object):
  def __init__(self, pixelMap, configReader, imageDim):
    """Initialize values"""
    self.pixelMap = pixelMap
    self.imageDim = imageDim
    self.patchWidth = configReader.sw_patchWidth
    self.patchHeight = configReader.sw_patchHeight
    self.binaryStructure = configReader.pe_binaryStructure
    self.curationPatchThresholds = configReader.pe_curationPatchThresholds
    self.maxCandidateIntersectionDiff = configReader.pe_maxCandidateIntersectionDiff
    self.maxSubsumedIntersectionDiff = configReader.pe_maxSubsumedIntersectionDiff

  def getPatchesForCuration(self):
    """Get all patches for this pixelMap that optimally reduces the number of
    times a pixel is seen by user during curation
    Returns an array of bounding box rectangles and associated threshold"""
    candidateBboxes = []
    # run through all thresholds
    for threshold in self.curationPatchThresholds:
      candidateBboxes += self.getPeakBboxes(threshold)
    # iteratively, combine candidateBboxes to get final patches
    subsumedBboxes = self.subsumeRectangles(candidateBboxes)
    return subsumedBboxes

  def BFS( self, maxima, index, visitedCells, potentialCells ):
    unvisitedCells = set()
    cb = maxima.cellBoundaries[ index ]
    unvisitedCells.add( ( cb[ 'x0' ], cb[ 'y0'], cb[ 'x3' ], cb[ 'y3' ], cb[ 'idx' ] ) )
    while len( unvisitedCells ) > 0:
      cb[ 'x0' ], cb[ 'y0'], cb[ 'x3' ], cb[ 'y3' ], cb[ 'idx' ] = unvisitedCells.pop()
      if ( cb[ 'x0' ], cb[ 'y0'], cb[ 'x3' ], cb[ 'y3' ], cb[ 'idx' ] ) in visitedCells:
        continue
      neighborCells = maxima.cellBoundariesDict[ 'neighbors' ][ ( cb[ 'x0' ], cb[ 'y0'], cb[ 'x3' ], cb[ 'y3' ], cb[ 'idx' ] ) ]
      for n in neighborCells:
        if potentialCells[ n[ "idx" ] ] and \
            ( n[ 'x0' ], n[ 'y0'], n[ 'x3' ], n[ 'y3' ] ) not in visitedCells:
          unvisitedCells.add( ( n[ 'x0' ], n[ 'y0'], n[ 'x3' ], n[ 'y3' ], n[ 'idx' ] ) )
      visitedCells.add(( cb[ 'x0' ], cb[ 'y0'], cb[ 'x3' ], cb[ 'y3' ], cb[ 'idx' ] ) )
    return visitedCells

  def getPeakBboxes(self, threshold):
    """Get bounding boxes for peaks above given threshold such that
    (a) if two peaks are not contiguous as determined by threshold and 
    binaryStructure, then two different bbox are returned
    (b) the intensity of the returned bbox is average for the whole box
    Returns an array of bounding box rectangles and associated average intensity"""
    threshold = 0.005
    candidateBboxes = []
    # zero out all pixels below threshold
    maxima = self.pixelMap.copy()
    diff = (maxima.cellValues > threshold)
    maxima.cellValues[diff == 0] = 0
    visitedCells = set( [] )
    islands = []
    for cb in maxima.cellBoundaries:
      if ( cb[ 'x0' ], cb[ 'y0'], cb[ 'x3' ], cb[ 'y3' ], cb[ 'idx' ] ) in visitedCells:
        continue
      value = maxima.cellValues[cb['idx']]
      if value > 0:
        cells = self.BFS( maxima, cb['idx'], visitedCells, diff )
        islands.append( cells )

    candidateBboxes = []
    for island in islands:
      x0List = set()
      y0List = set()
      x3List = set()
      y3List = set()
      indexList = set()
      for x0, y0, x3, y3, index in island:
        x0List.add( x0 )
        y0List.add( y0 )
        x3List.add( x3 )
        y3List.add( y3 )
        indexList.add( index )

      bbox = Rectangle.rectangle_from_endpoints(min( x0List ), min( y0List ),
          max( x3List ), max( y3List ) )
      avg = np.average( maxima.cellValues[ np.array( list( indexList ) ) ] )
      candidateBboxes += [{'bbox': bbox, 'intensity': avg }]

    return candidateBboxes

  def subsumeRectangles(self, candidateBboxes):
    """Merge nearby overlapping bboxes such that
    (a) bboxes with highest intensity gets selected in a particular region
    (b) bboxes conform to the patch extraction dimensional requirements (note: only square supported for now)
    Returns the merged bboxes"""
    subsumedBboxes = []
    subsumedBboxCounter = 0
    if len(candidateBboxes) <= 0:
      return subsumedBboxes
    # in the begining none of the boxes are subsumed
    for lbl in candidateBboxes:
      lbl['subsumed'] = False
    # Start iteration: get the highest non-subsumed bbox
    candidate = sorted(candidateBboxes, \
      key = lambda lbl: (not lbl['subsumed'], lbl['intensity']), \
      reverse = True)[0]
    # Continue iteration: until all boxes are subsumed
    while not candidate['subsumed']:
      cBbox = candidate['bbox']
      # patch extraction dimensional requirement - assume square for now
      maxWH = max(self.patchWidth, cBbox.width, self.patchHeight, cBbox.height)
      patch = Rectangle.rectangle_from_centers(cBbox.centerX, cBbox.centerY, maxWH, maxWH, self.imageDim)
      # subsume other candidates based on this patch
      for lbl in candidateBboxes:
        lblBbox = lbl['bbox']
        intersectionDiff = lblBbox.intersection(patch).area/lblBbox.area
        # print "Iter: " + str(subsumedBboxCounter) + ", intersectionDiff: " + \
        #   str(intersectionDiff) + ", Subsumed: " + str(lbl['subsumed'])
        if (not lbl['subsumed']) and (intersectionDiff > self.maxCandidateIntersectionDiff):
          lbl['subsumed'] = True
      # include this patch only if it doesn't significantly overlap with other already included patches
      includeThisPatch = True
      for subsumedBox in subsumedBboxes:
        lblBbox = subsumedBox['bbox']
        intersectionDiff = lblBbox.intersection(patch).area/lblBbox.area
        if (intersectionDiff > self.maxSubsumedIntersectionDiff):
          includeThisPatch = False
          break
      if includeThisPatch:
        patchIntensity = candidate['intensity']
        subsumedBboxes += [{'bbox': patch, 'intensity': patchIntensity,\
          'label': ("%d: %.2f" % (subsumedBboxCounter, patchIntensity))}]
        subsumedBboxCounter += 1
      # regardless of whether this candidate was included or not, subsume and carry loop forward
      candidate['subsumed'] = True
      candidate = sorted(candidateBboxes, \
        key = lambda lbl: (not lbl['subsumed'], lbl['intensity']), \
        reverse = True)[0]
    # finally, return all boxes
    return subsumedBboxes
