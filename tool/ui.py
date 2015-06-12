#!/usr/bin/env python

import multiprocessing, time, os, logging
import math, sys, glob
from postprocessing.task.Task import Task
from postprocessing.task.GenerateCellMap import GenerateCellMap

from config.Config import Config
from config.Status import Status
from config.Version import Version
from infra.Pipeline import Pipeline

def main():
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml> <input.queue> <output.queue>' % sys.argv[ 0 ]
    sys.exit(1)

  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.Queue()
  process( sys.argv[ 1 ], inputs, results )

def process( configFileName, inputs, results ):
  logging.basicConfig(
    format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
    level=logging.INFO, datefmt="%Y-%m-%d--%H:%M:%S"
    )
  config = Config( configFileName )
  status = Status()

  myPipeline = Pipeline( [
                          GenerateCellMap( config, status )
                          ], inputs, results )

  Version().logVersion()
  startTime = time.time()
  myPipeline.start()
  
  # Enqueue jobs as they come
  num_jobs = 2
  inputs.put( ( 1, [ 0.2 ] * 543 ) )
  inputs.put( ( 1, [ 0.4 ] * 543 ) )
  
  # Add a poison pill for each Worker
  num_consumers = multiprocessing.cpu_count()
  for i in xrange(num_consumers):
      inputs.put(None)
  
  # Wait for all of the inputs to finish
  myPipeline.join()
  endTime = time.time()
  logging.info( 'Took %s seconds' % ( endTime - startTime ) )
  
  # Start logging results
  for i in xrange(num_consumers + num_jobs):
      result = results.get()
      logging.info( 'Result: %s', result )
