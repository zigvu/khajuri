from config.Config import Config
import sys, random, math, logging
import multiprocessing, time, os, logging

from infra.Pipeline import Pipeline
from config.Config import Config
from config.Status import Status
from config.Version import Version

from tests.RandomRectGenerator import RandomAnnotationGenerator
from tests.MockLocalizationTask import MockLocalizationTask
from tests.Statistics import Statistics

NUMOFFRAMESTOEVAL = 1000
def printLocalizationStats( configFileName ):
  config = Config( configFileName )
  assert config.allCellBoundariesDict
  assert config.neighborMap
  
  status = Status( config )
  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.Queue()
  myPipeline = Pipeline( 
          [ MockLocalizationTask( config, status ) ],
          inputs, results )
  myPipeline.start()

  aGen = RandomAnnotationGenerator( config )
  frameNum = 0
  stats = Statistics( config )
  for a in aGen:
    logging.info( 'Adding %s into input' % a )
    inputs.put( a )
    frameNum += 1 
    if frameNum >= NUMOFFRAMESTOEVAL:
       break

  num_consumers = multiprocessing.cpu_count()
  for i in xrange(num_consumers):
    inputs.put(None)
 
  while frameNum > 0:
    singleFrameStat = results.get()
    if singleFrameStat:
      stats.addFrameStats( singleFrameStat )
      frameNum -= 1
      if len( stats.stats ) % 10 == 0:
        print 'Got %s results so far' % len( stats.stats )
  
  myPipeline.join()
  stats.printStat()
     
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
