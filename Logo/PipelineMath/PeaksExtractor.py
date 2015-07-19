import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle


class PeaksExtractor(object):
  """Extract peaks in PixelMap"""

  def __init__(self, pixelMap, config):
    """Initialize values"""
    self.pixelMap = pixelMap
    self.detectorThreshold = config.postProcessing.pp_detectorThreshold

  def getPeakBboxes(self):
    """Get bboxes for all peaks"""
    candidateBboxes = []

    # zero out all pixels below threshold
    maxima = self.pixelMap.copy()
    diff = (maxima.cellValues > self.detectorThreshold)
    maxima.cellValues[diff == 0] = 0

    # Find cell Indexes with a positive value
    posValueSet = set()
    for i in np.argwhere(diff):
      posValueSet.add(i[0])

    # Find Islands and Number them
    while len(posValueSet) > 0:
      i = posValueSet.pop()
      neighbors, maxValue, avgValue, cb = maxima.BFS(i)
      posValueSet.difference_update(neighbors.difference(set([i])))

      bbox = Rectangle.rectangle_from_endpoints(cb[0], cb[1], cb[2], cb[3])
      candidateBboxes.append({'bbox': bbox, 'intensity': avgValue})
    return candidateBboxes
