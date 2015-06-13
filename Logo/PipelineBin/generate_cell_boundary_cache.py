#!/usr/bin/env python 

import sys, os, glob, logging
from config.Config import Config

from Logo.PipelineMath.PixelMap import CellBoundaries
from Logo.PipelineMath.PixelMap import NeighborsCache
from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
import cPickle as pickle

def main():
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[ 0 ]
    sys.exit(1)
  logging.basicConfig(
    format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
    level=logging.INFO, datefmt="%Y-%m-%d--%H:%M:%S")

  configFileName = sys.argv[1]
  config = Config(configFileName)
  logging.info( 'Starting to get cell boundaries' )
  cellBoundaries = CellBoundaries( config )
  logging.info( 'Done with calculating cell boundaries.' )
  logging.info( 'Starting to calculate neighbors.' )
  neighborCache = NeighborsCache( config )
  neighbors = neighborCache.neighborMapAllScales( cellBoundaries.allCellBoundariesDict )
  logging.info( 'Done with calculating neighbors.' )

if __name__ == '__main__':
  main()
