#!/usr/bin/env python
import csv, glob, logging, sys, os
import matplotlib.pyplot as plt
import numpy as np
import json

description = \
"""
Using Model Performance Analysis
================================

    Usage model_performance_analysis.py <csv_folder> <score_threshold> 
    <count_threshold> <class_mapping> <output_folder> [ <patchImageFolder> ]

Parameters Description
======================
    <csv_folder>       - where the test scores csv files are located.
    <score_threshold>  - threshold above which we account for confusion
    <count_threshold>  - count threshold above which we account for confusion 
                         between two classes
    <class_mapping>    - label_mapping.txt file generated along with leveldb
    <output_folder>    - folder where this script should create its output
    <patchImageFolder> - Folder with all the patches.   

First Flow
==========
Supply all parameters except for patchImageFolder. This will only generate the 
patches.json in the outputFolder

Second Flow
===========
Supply all parameters including patchImageFolder. This will only generate the 
patches.json in the outputFolder  as well as copy over patches inside 
outputFolder. Patches are organized into folders with classA_classB - where 
the patch from classA was confused with classB.


The parameter inside the square bracket - patchImageFolder - is optional - 
since its used only in the first flow.
"""


class ConfusionPair(object):

  def __init__(self, k, v):
    self.key = k
    self.value = v

  def __lt__(self, other):
    if self.value < other.value:
      return True
    else:
      return False


def main():
  if len(sys.argv) < 6:
    print 'Usage %s ' % sys.argv[0] + \
        '<csv_folder> <score_threshold> <count_threshold> <class_mapping>' + \
        ' <output_folder> [ <patchImageFolder> ]'
    print description
    sys.exit(1)

  csvFolder = sys.argv[1]
  scoreThreshold = float(sys.argv[2])
  countThreshold = float(sys.argv[3])
  classMappingFile = sys.argv[4]
  outputFolder = sys.argv[5]
  if not os.path.exists(outputFolder):
    os.makedirs(outputFolder)

  patchImageFolder = None
  if len(sys.argv) == 7:
    patchImageFolder = sys.argv[6]

  # Logging levels
  logging.basicConfig(
      format=
      '{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=logging.INFO,
      datefmt="%Y-%m-%d--%H:%M:%S")

  logging.info('Using folder %s' % csvFolder)
  logging.info('Using score threshold %s' % scoreThreshold)
  logging.info('Using count threshold %s' % countThreshold)
  if patchImageFolder:
    logging.info('Using Image Patch Folder: %s' % patchImageFolder)

  scores = {}
  imgByClass = {}
  classMapping = {}
  f = open(classMappingFile, 'r')
  content = f.read()
  for l in content.split('\n'):
    if l:
      k, v = l.split()
      classMapping[v] = k

  for f in glob.glob(os.path.join(csvFolder, '*.csv')):
    logging.debug('Reading file %s' % f)
    with open(f, 'rb') as myFile:
      className = os.path.splitext(os.path.basename(f))[0]
      reader = csv.reader(myFile)
      header = False
      for row in reader:
        if not header:
          header = True
          continue
        else:
          # logging.debug( '%s' % row )
          imgByClass[row[0]] = className
          if len(row) > 0:
            for i in range(1, len(row)):
              scores[(row[0], classMapping["%s" % (i - 1)])] = float(row[i])
          else:
            break

  # Filter Using the scoreThreshold
  filteredScores = {}
  for k, v in scores.iteritems():
    if v >= scoreThreshold:
      filteredScores[k] = v

  countHeatMap = {}
  avgScoreHeatMap = {}
  patchListToExamine = {}
  for clsA in classMapping.values():
    for clsB in classMapping.values():
      countHeatMap[(clsA, clsB)] = 0
      avgScoreHeatMap[(clsA, clsB)] = 0
      if clsA != clsB:
        patchListToExamine[(clsA, clsB)] = []

  patchFileLocation = {}
  if patchImageFolder:
    for patchFile in glob.glob(os.path.join(patchImageFolder, "*", "*.png")):
      patchFileLocation[os.path.basename(patchFile)] = patchFile

  for k, v in filteredScores.iteritems():
    clsA = imgByClass[k[0]]
    clsB = k[1]
    countHeatMap[(clsA, clsB)] += 1
    if avgScoreHeatMap[(clsA, clsB)] == 0:
      avg = v
    else:
      avg = (avgScoreHeatMap[(clsA, clsB)] + v) / 2.0
    avgScoreHeatMap[(clsA, clsB)] = avg
    if v >= scoreThreshold and clsA != clsB:
      patchListToExamine[(clsA, clsB)].append({'patch': k[0], 'score': v})
      if patchImageFolder:
        outputDir = os.path.join(outputFolder, "%s_%s" % (clsA, clsB))
        if not os.path.exists(outputDir):
          os.makedirs(outputDir)
        inputPatchPath = os.path.join(patchImageFolder, clsA, k[0])
        if not os.path.exists(inputPatchPath):
          logging.debug('Missing Patch %s' % inputPatchPath)
        else:
          logging.debug('Copying Patch %s to %s' % (
              inputPatchPath, os.path.join(outputDir, k[0])
          ))
          os.system('cp %s %s' %
                    (inputPatchPath, os.path.join(outputDir, k[0])))

  patchDumpJsonFile = os.path.join(outputFolder, "patches.json")
  patchListToExamineForJson = {}
  logging.info('Dumping patches into %s' % patchDumpJsonFile)
  for k, v in patchListToExamine.iteritems():
    if not v:
      continue
    patchListToExamineForJson["(%s,%s)" % k] = v
  json.dump(patchListToExamineForJson, open(patchDumpJsonFile, 'w'), indent=2)

  confusionCountFile = os.path.join(outputFolder, "confusionCount.txt")
  logging.info('Confusion Counts greater than %s produce in file %s' %
               (countThreshold, confusionCountFile))
  confusionAvgCountList = []
  for k, v in countHeatMap.iteritems():
    if k[0] == k[1]:
      continue
    if v >= countThreshold:
      confusionAvgCountList.append(ConfusionPair(k, v))
  with open(confusionCountFile, 'w') as f:
    for p in sorted(confusionAvgCountList):
      f.write('%s, %s : %s\n' % (p.key[0], p.key[1], p.value))

  confusionAvgScoreFile = os.path.join(outputFolder, "confusionAvgScore.txt")
  logging.info('ConfusionAvg Scores greater than %s produce in %s' %
               (scoreThreshold, confusionAvgScoreFile))
  confusionAvgScoreList = []
  for k, v in avgScoreHeatMap.iteritems():
    if k[0] == k[1]:
      continue
    if v >= scoreThreshold:
      confusionAvgScoreList.append(ConfusionPair(k, v))
  with open(confusionAvgScoreFile, 'w') as f:
    for p in sorted(confusionAvgScoreList):
      f.write('%s, %s : %s\n' % (p.key[0], p.key[1], p.value))


if __name__ == '__main__':
  main()
