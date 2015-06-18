#!/usr/bin/env python

import multiprocessing, time, os, logging
import math, sys, glob

from config.Config import Config
from config.Status import Status
from config.Version import Version

from infra.Pipeline import Pipeline

from postprocessing.task.Task import Task
from postprocessing.task.ClassFilter import ClassFilter
from postprocessing.task.ZDistFilter import ZDistFilter
from postprocessing.task.JsonReader import JsonReader
from postprocessing.task.OldJsonReader import OldJsonReader
from postprocessing.task.Localization import Localization
from postprocessing.task.PostProcess import PostProcess


def main():
  if len(sys.argv) < 4:
    print 'Usage %s <config.yaml> <jsonFolder> <jsonOutputFolder>' % sys.argv[0]
    sys.exit(1)
  os.makedirs(sys.argv[3])
  process(sys.argv[1], sys.argv[2], sys.argv[3])


def process(configFileName, jsonFolder, jsonOutputFolder):
  logging.basicConfig(
      format=
      '{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=logging.INFO,
      datefmt="%Y-%m-%d--%H:%M:%S")
  config = Config(configFileName)
  config.json_output_folder = jsonOutputFolder
  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.Queue()
  status = Status()

  #Uncomment for serial run
  #reader = OldJsonReader( config, status ),
  #classFilter = ClassFilter( config, status ),
  #zDist = ZDistFilter( config, status ),
  #localization = Localization( config, status )

  #for jsonFile in glob.glob( jsonFolder + os.sep + "*.json" ):
  #  postprocess = PostProcess( config, status )
  #  postprocess( jsonFile )

  #return
  #myPipeline = Pipeline( [
  #                        OldJsonReader( config, status ),
  #                        ClassFilter( config, status ),
  #                        #ZDistFilter( config, status ),
  #                        Localization( config, status )
  #                        ], inputs, results )
  config.videoId = None
  myPipeline = Pipeline([PostProcess(config, status)], inputs, results)

  Version().logVersion()
  startTime = time.time()
  myPipeline.start()

  # Enqueue jobs
  num_jobs = 0
  for jsonFile in glob.glob(jsonFolder + os.sep + "*.json"):
    inputs.put(jsonFile)
    num_jobs += 1

  # Add a poison pill for each Worker
  num_consumers = multiprocessing.cpu_count()
  for i in xrange(num_consumers):
    inputs.put(None)

  # Wait for all of the inputs to finish
  myPipeline.join()
  endTime = time.time()
  logging.info('Took %s seconds' % (endTime - startTime))

  # Start logging results
  for i in xrange(num_consumers + num_jobs):
    result = results.get()
    logging.info('Result: %s', result)
