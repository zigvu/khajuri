#!/usr/bin/env python

import multiprocessing, time, os, logging
import math, sys, glob
from postprocessing.task.Task import Task
from postprocessing.task.ClassFilter import ClassFilter
from postprocessing.task.ZDistFilter import ZDistFilter
from postprocessing.task.JsonReader import JsonReader
from postprocessing.config.Config import Config
from postprocessing.config.Status import Status
from postprocessing.infra.Pipeline import Pipeline

def main():
  if len(sys.argv) < 3:
    print 'Usage %s <config.yaml> <jsonFolder>' % sys.argv[ 0 ]
    sys.exit(1)

  config = Config( sys.argv[ 1 ] )
  logging.basicConfig(
    format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
    level=logging.INFO, datefmt="%Y-%m-%d--%H:%M:%S",
    filename=config.log_file )
  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.Queue()
  status = Status()
  
  myPipeline = Pipeline( [
                          JsonReader( config, status ),
                          ClassFilter( config, status ),
                          ZDistFilter( config, status )
                          ], inputs, results )
  myPipeline.start()
  
  # Enqueue jobs
  num_jobs = 0
  for jsonFile in glob.glob( sys.argv[ 2 ] + os.sep + "*.json" ):
    inputs.put( jsonFile )
    num_jobs += 1
  
  # Add a poison pill for each Worker
  num_consumers = multiprocessing.cpu_count()
  for i in xrange(num_consumers):
      inputs.put(None)
  
  # Wait for all of the inputs to finish
  myPipeline.join()
  
  # Start logging results
  for i in xrange(num_consumers + num_jobs):
      result = results.get()
      logging.info( 'Result: %s', result )
