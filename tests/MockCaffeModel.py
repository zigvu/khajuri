import sys, random, math, logging

import numpy as np

from postprocessing.type.Rect import Rect

class MockCaffeModel( object ):

  def __init__( self, config ):
    self.cellBoundariesDict = config.allCellBoundariesDict
    self.patchMapping = self.cellBoundariesDict[ "patchMapping" ]
    self.classIds = config.ci_allClassIds
    self.config = config

  def rectIntersect( self, patchDim, annotations ):
    scale = patchDim[ 0 ]
    patchRect = Rect(
        patchDim[ 1 ]/scale, 
        patchDim[ 2 ]/scale,
        patchDim[ 3 ]/scale - patchDim[ 1 ]/scale, 
        patchDim[ 4 ]/scale - patchDim[ 2 ]/scale
        )
    for a in annotations:
        areaIntersect = patchRect.intersect( a )
        if areaIntersect > ( 0.8 * a.area ):
            return True
        else:
            continue
    return False

  def probPatch( self, patchDim, annotations ):
    if self.rectIntersect( patchDim, annotations ):
      prob = np.zeros(  ( 1, len( self.classIds ) ) )
      prob[ 0, 0 ] = 1
    else:
      prob = np.random.random( ( 1, len( self.classIds ) ) )
      prob = prob / np.sum( prob )
    return prob

  def scoreFrame( self, annotatedFrame ):
    frame = annotatedFrame.frame
    annotations = annotatedFrame.annotations
    # Generate Prob Scores
    for patchDim, patchId in self.patchMapping.iteritems():
      frame.scores[ 0 ] [ patchId, :, 0 ] = self.probPatch( patchDim, annotations )
