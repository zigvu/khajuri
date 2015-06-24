#!/usr/bin/env python

import multiprocessing, time, os
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
  config = Config(configFileName)
  logger = config.logger
  status = Status(logger)

  config.json_output_folder = jsonOutputFolder
  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.Queue()

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

  branch, commit = Version().getGitVersion()
  logger.info('Branch: %s' % branch)
  logger.info('Commit: %s' % commit)

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
  logger.info('Took %s seconds' % (endTime - startTime))

  # Start printing results
  for i in xrange(num_consumers + num_jobs):
    result = results.get()
    logger.info('Result: %s', result)
