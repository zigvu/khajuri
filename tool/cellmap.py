#!/usr/bin/env python

import multiprocessing, time, os, logging
import math, sys, glob
import numpy as np
from postprocessing.task.Task import Task
from config.Config import Config
from config.Status import Status
from config.Version import Version
from infra.Pipeline import Pipeline

from Logo.PipelineMath.PixelMap import PixelMap

class CellMapTask( Task ):
  def __call__( self, obj ):
    patchScores, scaleFactor = obj
    pixelMap = PixelMap( self.config.allCellBoundariesDict, scaleFactor )
    pixelMap.addScore( patchScores )
    return ( pixelMap.cellValues )

def main():
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[ 0 ]
    sys.exit(1)
  process( sys.argv[ 1 ] )

def process( configFileName ):
  config = Config( configFileName )
  status = Status()
  cellMapTask = CellMapTask( config, status )
  numOfPatches = len( config.allCellBoundariesDict[ "patchMapping" ].keys() )

  scales = [ 0.7, 1, 1.3 ]
  for i in range( 0, 10 ):
    patchScores = np.random.random( numOfPatches)
    for scale in scales:
      print 'At Scale %s, patchScores %s => cellValues %s' % ( scale, patchScores, cellMapTask( ( patchScores, scale ) ) )

if __name__=="__main__":
  main()
