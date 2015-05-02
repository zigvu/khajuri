import numpy as np
import scipy.ndimage as ndimage

from Logo.PipelineMath.Rectangle import Rectangle
import matplotlib.pyplot as plt

class PeaksExtractor(object):
  def __init__(self, pixelMap, config):
    """Initialize values"""
    self.pixelMap = pixelMap
    self.config = config

  def getPeakBboxes(self):
    candidateBboxes = []

    # zero out all pixels below threshold
    maxima = self.pixelMap.copy()
    diff = (maxima.cellValues > self.config.pp_detectorThreshold)
    maxima.cellValues[diff == 0] = 0

    # Find cell Indexes with a positive value
    posValueSet = set()
    for i in np.argwhere( diff ):
      posValueSet.add( i[0] )

    # Find Islands and Number them
    while len( posValueSet ) > 0:
      i = posValueSet.pop()
      neighbors, maxValue, avgValue, cb = maxima.BFS( i )
      for n in neighbors:
        if n != i:
          posValueSet.discard( n )
      bbox = Rectangle.rectangle_from_endpoints(cb[0], cb[1], cb[2], cb[3])
      candidateBboxes.append( { 'bbox': bbox, 'intensity' : avgValue } )
    return candidateBboxes
