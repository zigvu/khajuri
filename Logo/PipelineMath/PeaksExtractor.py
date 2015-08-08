import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle
import matplotlib.pyplot as plt


class PeaksExtractor(object):
  """Extract peaks in PixelMap"""

  def __init__(self, pixelMap, config):
    """Initialize values"""
    self.pixelMap = pixelMap
    self.config = config

  def getPeakBboxes(self):
    """Get bboxes for all peaks"""
    candidateBboxes = []
    
    # Find unique values
    #uniques = np.unique( self.pixelMap.cellValues )
    #uniques = len( uniques) * ( 2.0/3.0 )

    #myArray = self.pixelMap.cellValues
    #threshold = np.min(myArray[ np.argpartition(myArray, -uniques)[-uniques:] ])
    #threshold = self.config.pp_detectorThreshold
    #threshold = np.percentile(  self.pixelMap.cellValues, 70 )
    threshold = 0.1

    # zero out all pixels below threshold
    maxima = self.pixelMap.copy()
    diff = ( maxima.cellValues > threshold )
    maxima.cellValues[diff == 0] = 0

    # Save the maxima 
    #plt.imshow( maxima.toNumpyArray() ).write_png( 'peaksExtractor.png' )


    # Find cell Indexes with a positive value
    posValueSet = set()
    for i in np.argwhere(diff):
      posValueSet.add(i[0])

    # Find Islands and Number them
    while len(posValueSet) > 0:
      i = np.argmax( maxima.cellValues )
      neighbors, maxValue, avgValue, cb = maxima.BFS(i, 0.2 )
      posValueSet.difference_update(neighbors.difference(set([i])))
      assert maxima.cellValues[ i ] == maxValue
      posValueSet.remove( i )
      maxima.cellValues[ i ] = 0
      maxima.cellValues[ list( neighbors ) ] = 0
      bbox = Rectangle.rectangle_from_endpoints(cb[0], cb[1], cb[2], cb[3])
      candidateBboxes.append({'bbox': bbox, 'intensity': avgValue})
    return candidateBboxes
