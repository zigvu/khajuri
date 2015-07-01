#!/usr/bin/env python

import multiprocessing, time, os
import math, sys, glob

from config.Config import Config
from config.Status import Status
from config.Version import Version

from infra.Pipeline import Pipeline

from postprocessing.task.Task import Task
from postprocessing.task.GenerateCellMap import GenerateCellMap


def main():
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml> <input.queue> <output.queue>' % sys.argv[0]
    sys.exit(1)

  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.Queue()
  process(sys.argv[1], inputs, results)


def process(configFileName, inputs, results):
  config = Config(configFileName)
  logger = config.logging.logger

  status = Status(logger)

  myPipeline = Pipeline([GenerateCellMap(config, status)], inputs, results)

  branch, commit = Version().getGitVersion()
  logger.info('Branch: %s' % branch)
  logger.info('Commit: %s' % commit)

  startTime = time.time()
  myPipeline.start()

  # Enqueue jobs as they come
  num_jobs = 2
  inputs.put((1, [0.2] * 543))
  inputs.put((1, [0.4] * 543))

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
