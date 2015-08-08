#!/usr/bin/env python
from config.Config import Config
import sys, random, math, logging
import multiprocessing, time, os, logging

from infra.Pipeline import Pipeline
from config.Config import Config
from config.Status import Status
from config.Version import Version

from tests.RandomRectGenerator import MAXANNOTATIONPERFRAME
from tests.MockLocalizationTask import MockLocalizationTask
from tests.Statistics import Statistics
from AnnotatedFrame import FrameDumpWriter
from AnnotatedFrame import AnnotatedFrame
from DrawFrame import drawImage
from postprocessing.type.Rect import Rect
from AnnotatedFrame import FrameDumpReader

import matplotlib.pyplot as plt
import texttable

def printPlots( statsByScale ):
  plots = []
  legends = []
  for key, value in sorted( statsByScale.iteritems() ):
    plt.subplot( 1, 2, 1 )
    f1, = plt.plot( sorted( value.areaRatio ) )
    plots.append( f1 )
    legends.append( '%s' % key ) 
  plt.legend( plots, legends )
  plots = []
  legends = []
  for key, value in sorted( statsByScale.iteritems() ):
    plt.subplot( 1, 2, 2 )
    f1, = plt.plot( sorted( value.centerDistance ) )
    plots.append( f1 )
    legends.append( '%s' % key ) 
  plt.legend( plots, legends )

  plt.subplot( 1, 2, 1 )
  plt.ylabel( 'Area Ratio' )
  plt.subplot( 1, 2, 2 )
  plt.ylabel( 'Center Distance' )
  plt.savefig( 'Stats.png' )
  plt.close()

 
def printLocalizationStats( configFileName, annotationsFile ):
  config = Config( configFileName )
  assert config.allCellBoundariesDict
  assert config.neighborMap
  
  status = Status( config )
  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.JoinableQueue()
  myPipeline = Pipeline( 
          [ MockLocalizationTask( config, status ) ],
          inputs, results )
  myPipeline.start()
  fdr = FrameDumpReader( annotationsFile,
          MAXANNOTATIONPERFRAME )
  frameNum = 0
  for f in fdr:
    inputs.put( f )
    frameNum += 1 
    if frameNum >= 100:
      break

  num_consumers = multiprocessing.cpu_count()
  for i in xrange(num_consumers):
    inputs.put(None)
 
  x = texttable.Texttable()
  x.add_row( [ 
          "NumOfAnnotations",
          "NumOfLocalizations",
          "ExtraLocalization",
          "MissingLocalization",
          "Enclosed",
          ] )
  while frameNum > 0:
    logging.info( 'Waiting for results' )
    singleFrameStat = results.get()
    results.task_done()
    if singleFrameStat:
      frameNum -= 1
      x.add_row( singleFrameStat.values() )
  
  myPipeline.join()
  print x.draw()

    
def main():
  if len(sys.argv) < 3:
    print 'Usage %s <config.yaml> <annotations.file> ' % sys.argv[ 0 ]
    sys.exit(1)
  #logging.basicConfig(
  #    format=
  #    '{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
  #    level=logging.INFO,
  #    datefmt="%Y-%m-%d--%H:%M:%S")
  printLocalizationStats( sys.argv[ 1 ], sys.argv[ 2 ] )

if __name__=="__main__":
  main()

