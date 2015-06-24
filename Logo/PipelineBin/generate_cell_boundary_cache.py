#!/usr/bin/env python

import sys, os, glob

from config.Config import Config

from Logo.PipelineMath.PixelMap import CellBoundaries
from Logo.PipelineMath.PixelMap import NeighborsCache
from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
import cPickle as pickle

description = \
"""
This script will generate cell boundaries for use in PixelMap
"""

def main():
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    print description
    sys.exit(1)
  configFileName = sys.argv[1]
  config = Config(configFileName)
  self.logger = config.logger

  self.logger.info('Start: Get cell boundaries')
  cellBoundaries = CellBoundaries(config)
  self.logger.info('Done: Getting cell boundaries.')
  self.logger.info('Start: Get cell neighbors.')
  neighborCache = NeighborsCache(config)
  neighbors = neighborCache.neighborMapAllScales(
      cellBoundaries.allCellBoundariesDict)
  self.logger.info('Done: Getting cell neighbors.')


if __name__ == '__main__':
  main()
