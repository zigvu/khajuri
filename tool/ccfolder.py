#!/usr/bin/python

import sys, os, glob, logging, multiprocessing
import time
from collections import OrderedDict

from config.Config import Config
from config.Status import Status
from config.Version import Version

from infra.Pipeline import Pipeline

from postprocessing.task.CompareFiles import CompareFiles
from postprocessing.task.OldJsonReader import OldJsonReader
from postprocessing.task.JsonReader import JsonReader


def displayDiff(
    classes, adiffMax, adiffAvg, adiffMin, aDiffNumBboxesLoc,
    aDiffScoreOfBboxesLoc):
  print "\n\nPatch Score Max\nclass,score,frameNumber"
  for cls in classes:
    print "%s,%0.3f,%s" % (
        cls, adiffMax[cls]['value'], adiffMax[cls]['frameNumber']
    )

  print "\n\nPatch Score Avg\nclass,score,frameNumber"
  for cls in classes:
    print "%s,%0.3f,%s" % (
        cls, adiffAvg[cls]['value'], adiffAvg[cls]['frameNumber']
    )

  print "\n\nPatch Score Min\nclass,score,frameNumber"
  for cls in classes:
    print "%s,%0.3f,%s" % (
        cls, adiffMin[cls]['value'], adiffMin[cls]['frameNumber']
    )

  print "\n\nLocalization Num Bbox Diff\nclass,score,frameNumber"
  for cls in classes:
    print "%s,%0.3f,%s" % (
        cls, aDiffNumBboxesLoc[cls]['value'],
        aDiffNumBboxesLoc[cls]['frameNumber'])

  print "\n\nLocalization Score Diff\nclass,score,frameNumber"
  for cls in classes:
    print "%s,%0.3f,%s" % (
        cls, aDiffScoreOfBboxesLoc[cls]['value'],
        aDiffScoreOfBboxesLoc[cls]['frameNumber'])


def main():
  if len(sys.argv) < 6:
    print 'Usage %s ' % sys.argv[0] + \
      '<config.yaml> <folder1> <old/new> <folder2> <old/new>'
    print 'This executable will compare two folders and print any diff per class'
    sys.exit(1)
  logging.basicConfig(
      format=
      '{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=logging.INFO,
      datefmt="%Y-%m-%d--%H:%M:%S")

  config = Config(sys.argv[1])
  config.videoId = None
  Version().logVersion()
  status = Status()

  startTime = time.time()
  f1 = sys.argv[2]
  f1Format = sys.argv[3]
  f2 = sys.argv[4]
  f2Format = sys.argv[5]

  inputs = multiprocessing.JoinableQueue()
  results = multiprocessing.Queue()

  classes = config.ci_allClassIds
  adiffMax = OrderedDict()
  adiffAvg = OrderedDict()
  adiffMin = OrderedDict()

  aDiffNumBboxesLoc = OrderedDict()
  aDiffScoreOfBboxesLoc = OrderedDict()
  aDiffNumBboxesCur = OrderedDict()
  aDiffScoreOfBboxesCur = OrderedDict()

  for cls in classes:
    adiffMax[cls] = {'value': -1, 'frameNumber': None}
    adiffAvg[cls] = {'value': 0, 'frameNumber': None}
    adiffMin[cls] = {'value': 999, 'frameNumber': None}

    aDiffNumBboxesLoc[cls] = {'value': 0, 'frameNumber': None}
    aDiffScoreOfBboxesLoc[cls] = {'value': -1, 'frameNumber': None}
    aDiffNumBboxesCur[cls] = {'value': 0, 'frameNumber': None}
    aDiffScoreOfBboxesCur[cls] = {'value': -1, 'frameNumber': None}

  myPipeline = Pipeline([CompareFiles(config, status)], inputs, results)
  myPipeline.start()

  # Glob all files from the first folder, match it with the second one, 
  # put into the queue
  num_jobs = 0
  for j in glob.glob(os.path.join(f1, "*.json")):
    k = os.path.join(f2, os.path.basename(j))
    inputs.put((j, f1Format, k, f2Format))
    num_jobs += 1

  num_consumers = multiprocessing.cpu_count()
  for i in xrange(num_consumers):
    inputs.put(None)
  myPipeline.join()
  endTime = time.time()
  logging.info('Took %s seconds' % (endTime - startTime))

  scoreDiff = []
  localizationDiff = []
  for i in xrange(num_consumers + num_jobs):
    result = results.get()
    if not result:
      continue
    scoreDiff = result[1]
    localizationDiff = result[2]
    frameNumber = result[0].frameNumber
    for cls in classes:
      if scoreDiff[cls]['max'] > adiffMax[cls]['value']:
        adiffMax[cls]['value'] = scoreDiff[cls]['max']
        adiffMax[cls]['frameNumber'] = frameNumber

      if scoreDiff[cls]['avg'] > adiffAvg[cls]['value']:
        adiffAvg[cls]['value'] = scoreDiff[cls]['avg']
        adiffAvg[cls]['frameNumber'] = frameNumber

      if scoreDiff[cls]['min'] < adiffMin[cls]['value']:
        adiffMin[cls]['value'] = scoreDiff[cls]['min']
        adiffMin[cls]['frameNumber'] = frameNumber

      if localizationDiff[cls]['bbox'] > aDiffNumBboxesLoc[cls]['value']:
        aDiffNumBboxesLoc[cls]['value'] = localizationDiff[cls]['bbox']
        aDiffNumBboxesLoc[cls]['frameNumber'] = frameNumber

      if localizationDiff[cls]['maxS'] > aDiffScoreOfBboxesLoc[cls]['value']:
        aDiffScoreOfBboxesLoc[cls]['value'] = localizationDiff[cls]['maxS']
        aDiffScoreOfBboxesLoc[cls]['frameNumber'] = frameNumber

  displayDiff(
      classes, adiffMax, adiffAvg, adiffMin, aDiffNumBboxesLoc,
      aDiffScoreOfBboxesLoc)


if __name__ == '__main__':
  main()
