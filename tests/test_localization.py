#!/usr/bin/env python
from config.Config import Config
import sys, random, math, logging
import multiprocessing, time, os, logging

from infra.Pipeline import Pipeline
from config.Config import Config
from config.Status import Status
from config.Version import Version

from tests.RandomRectGenerator import RandomAnnotationGenerator
from tests.RandomRectGenerator import MAXANNOTATIONPERFRAME
from tests.MockLocalizationTask import MockLocalizationTask
from tests.Statistics import Statistics
from AnnotatedFrame import FrameDumpWriter
from AnnotatedFrame import AnnotatedFrame
from DrawFrame import drawImage
from postprocessing.type.Rect import Rect

NUMOFFRAMESTOEVAL = 100
def printLocalizationStats( configFileName ):
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

  aGen = RandomAnnotationGenerator( config )
  frameNum = 0
  for a in aGen:
    inputs.put( a )
    frameNum += 1 
    if frameNum >= NUMOFFRAMESTOEVAL:
       break
  #frameNum = 0
  #a = AnnotatedFrame()
  ##a.addAnnotation( Rect( 549, 95, 116, 34 ) )
  #a.addAnnotation( Rect( 680, 145, 160, 160 ) )
  ##a.addAnnotation( Rect( 50, 300, 150, 116 ) )
  ##a.addAnnotation( Rect( 700, 530, 100, 100 ) )
  ##a.addAnnotation( Rect( 1000, 100, 130, 130 ) )
  #a.frameNum = frameNum
  #frameNum += 1
  #inputs.put( a )
  statsByScale = {}
  for scale in config.sw_scales:
    statsByScale[ scale ] = Statistics( config, scale )

  num_consumers = multiprocessing.cpu_count()
  for i in xrange(num_consumers):
    inputs.put(None)
 
  while frameNum > 0:
    logging.info( 'Waiting for results' )
    singleFrameStat = results.get()
    results.task_done()
    if singleFrameStat:
      #drawImage( singleFrameStat, frameNum, config )
      logging.info( 'Adding %s to result set' % singleFrameStat )
      statsByScale[ singleFrameStat.localizationScale[0] ].addFrameStats( singleFrameStat )
      frameNum -= 1
  
  myPipeline.join()
  for key, value in statsByScale.iteritems():
    print 'Displaying result at scale %s' % key
    value.printStat()
     
if __name__=="__main__":
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[ 0 ]
    sys.exit(1)
  #logging.basicConfig(
  #    format=
  #    '{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
  #    level=logging.INFO,
  #    datefmt="%Y-%m-%d--%H:%M:%S")
  printLocalizationStats( sys.argv[ 1 ] )
