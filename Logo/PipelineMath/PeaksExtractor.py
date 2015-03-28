import numpy as np
import scipy.ndimage as ndimage

from Logo.PipelineMath.Rectangle import Rectangle
import matplotlib.pyplot as plt

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

  def getPeakBboxes( self, threshold ):
    return self.getPeakBboxesUsingCellMap( threshold )

  def getPeakBboxesUsingCellMap(self, threshold):
    """Get bounding boxes for peaks above given threshold such that
    (a) if two peaks are not contiguous as determined by threshold and 
    binaryStructure, then two different bbox are returned
    (b) the intensity of the returned bbox is average for the whole box
    Returns an array of bounding box rectangles and associated average intensity"""
    candidateBboxes = []

    # zero out all pixels below threshold
    maxima = self.pixelMap.copy()
    diff = (maxima.cellValues > threshold)
    maxima.cellValues[diff == 0] = 0

    # Find cell Indexes with a positive value
    posValueSet = set()
    for i in np.argwhere( diff ):
      posValueSet.add( i[0] )

    # Find Islands and Number them
    islands = []
    while len( posValueSet ) > 0:
      i = posValueSet.pop()
      neighbors, maxValue, avgValue, cb = maxima.BFS( i )
      for n in neighbors:
        if n != i:
          posValueSet.discard( n )
      bbox = Rectangle.rectangle_from_endpoints(cb[0], cb[1], cb[2], cb[3])
      candidateBboxes.append( { 'bbox': bbox, 'intensity' : avgValue } )
      islands.append( neighbors )
    return candidateBboxes

  def getPeakBboxesUsingNumpy(self, threshold):
    """Get bounding boxes for peaks above given threshold such that
    (a) if two peaks are not contiguous as determined by threshold and 
    binaryStructure, then two different bbox are returned
    (b) the intensity of the returned bbox is average for the whole box
    Returns an array of bounding box rectangles and associated average intensity"""
    candidateBboxes = []
    # zero out all pixels below threshold
    maxima = self.pixelMap.toNumpyArray().copy()
    diff = (maxima > threshold)
    maxima[diff == 0] = 0
    # label each non-contiguous area with integer values
    labeledArray, num_objects = ndimage.label(maxima, structure= self.binaryStructure)
    # find center of each labeled non-contiguous area
    xy = np.array(ndimage.center_of_mass(maxima, labeledArray, range(1, num_objects + 1)))
    # find bounding boxes
    for idx, coord in enumerate(xy):
      # zero out all pixels that don't belong to this label
      labelArea = labeledArray == (idx + 1)
      # find end points of the array containing label
      labelWhere = np.argwhere(labelArea)
      (yStart, xStart), (yEnd, xEnd) = labelWhere.min(0), labelWhere.max(0) + 1
      # create bbox based on the label
      bbox = Rectangle.rectangle_from_endpoints(xStart, yStart, xEnd, yEnd)
      # get the average intensity of the bbox
      avgIntensity = np.average(self.pixelMap.toNumpy()[yStart:yEnd, xStart:xEnd][labelArea[yStart:yEnd, xStart:xEnd]])
      candidateBboxes += [{'bbox': bbox, 'intensity': avgIntensity}]
      #candidateBboxes += [{'bbox': bbox, 'intensity': avgIntensity, 'label': ("%.2f" % avgIntensity)}]
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
