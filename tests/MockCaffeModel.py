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
        patchDim[ 1 ], 
        patchDim[ 2 ],
        patchDim[ 3 ] - patchDim[ 1 ], 
        patchDim[ 4 ] - patchDim[ 2 ]
        )
    logging.info( 'Patch is %s at scale %s' % ( patchRect, scale ) )
    for a in annotations:
        logging.info( 'Annotation is %s' % a )
        scaledAnnotation = Rect( a.x * scale, a.y * scale, a.w * scale, a.h * scale )
        logging.info( 'Scaled Annotation is %s at scale %s' % ( scaledAnnotation, scale ) )
        if scaledAnnotation.area <= ( 0.07 * ( 256 * 256 ) ):
          logging.info( 'Scaled Annotation is too small %s, should be at least %s at scale %s' % ( scaledAnnotation.area, 
                      ( 0.07  * 256 * 256 ), scale ) )
          continue
        areaIntersect = patchRect.intersect( scaledAnnotation )
        if areaIntersect >= ( 0.8 * scaledAnnotation.area ):
          logging.info( 'Scale Annotation is large enough at scale %s' % scale )
          return True
        else:
          logging.info( 'Scaled Annotation intersect is too small %s, should be at least %s at scale %s' % ( areaIntersect,
                      ( 0.8  * scaledAnnotation.area ), scale ) )
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
