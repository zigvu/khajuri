#!/usr/bin/env python

import sys
import os
import glob

import cPickle as pickle

from config.Config import Config

from Logo.PipelineMath.PixelMap import CellBoundaries
from Logo.PipelineMath.PixelMap import NeighborsCache

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
  logger = config.logging.logger

  logger.info('Start: Get cell boundaries')
  cellBoundaries = CellBoundaries(config)
  logger.info('Done: Getting cell boundaries.')
  logger.info('Start: Get cell neighbors.')
  neighborCache = NeighborsCache(config)
  neighbors = neighborCache.neighborMapAllScales(
      cellBoundaries.allCellBoundariesDict)
  logger.info('Done: Getting cell neighbors.')


if __name__ == '__main__':
  main()
