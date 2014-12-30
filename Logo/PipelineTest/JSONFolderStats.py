import sys, os, glob, math
import logging
from collections import OrderedDict
import numpy as np

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter

class JSONFolderStats( object ):
  def __init__( self, jsonFolder1, jsonFolder2 ):
    """Initialize"""
    self.jsonFolder1Files = glob.glob("%s/*.json" % jsonFolder1) + glob.glob("%s/*.gz" % jsonFolder1)
    self.jsonFolder2Files = glob.glob("%s/*.json" % jsonFolder2) + glob.glob("%s/*.gz" % jsonFolder2)

    # error checking
    self.numOfFiles = len(self.jsonFolder1Files)
    if self.numOfFiles != len(self.jsonFolder2Files):
      raise RuntimeError("Number of files in folders not same")
    for f1 in self.jsonFolder1Files:
      hasFile = False
      for f2 in self.jsonFolder2Files:
        if os.path.basename(f1) == os.path.basename(f2):
          hasFile = True
          break
      if not hasFile:
        raise RuntimeError("File %s not present in both folders" % f1)
    print "Done error checking folders"

    self.jrw1 = JSONReaderWriter(self.jsonFolder1Files[0])
    self.classes = self.jrw1.getClassIds()
    self.scales = self.jrw1.getScalingFactors()


    # sort json files by frame number
    print "Sorting %d files" % self.numOfFiles
    frameIndex = {}
    for f in self.jsonFolder1Files:
      jsonReaderWriter = JSONReaderWriter(f)
      frameNumber = jsonReaderWriter.getFrameNumber()
      frameIndex[frameNumber] = f
    self.jsonFolder1Files = []
    for frameNumber in sorted(frameIndex.keys()):
      self.jsonFolder1Files += [frameIndex[frameNumber]]
    print "Done with sorting files"

    # read all patch scores
    self.folder1Scores = OrderedDict()
    self.folder2Scores = OrderedDict()
    self.scoresDiff = OrderedDict()
    for cls in self.classes:
      self.folder1Scores[cls] = []
      self.folder2Scores[cls] = []
      self.scoresDiff[cls] = []

    fileCount = 0
    for f in self.jsonFolder1Files:
      jsonFile = os.path.basename(f)
      jrw1 = JSONReaderWriter(os.path.join(jsonFolder1, jsonFile))
      jrw2 = JSONReaderWriter(os.path.join(jsonFolder2, jsonFile))
      print "Working on file %s" % jsonFile
      for scale in self.scales:
        patches1 = jrw1.getPatches(scale)
        patches2 = jrw2.getPatches(scale)
        for patch1 in patches1:
          patchFileName1 = patch1['patch_filename']
          patchScores1 = patch1['scores']
          # match with the same patch name in jrw2
          patchFileName2 = None
          patchScores2 = None
          for patch2 in patches2:
            patchFileName2 = patch2['patch_filename']
            patchScores2 = patch2['scores']
            if patchFileName1 == patchFileName2:
              break
          if patchFileName2 == None:
            raise RuntimeError("No score for patch %s in JSON file %s" % (patchFileName1, jsonFile))
          # store in OrderDict:
          for cls in self.classes:
            self.folder1Scores[cls] += [patchScores1[cls]]
            self.folder2Scores[cls] += [patchScores2[cls]]
            self.scoresDiff[cls] += [abs(patchScores1[cls] - patchScores2[cls])]
      # increase counters
      fileCount += 1
      if fileCount % 100 == 0:
        print "Ingested %d percent of all files" % (int(fileCount * 100.0 / self.numOfFiles))
    # for each class, all scores are read into dictionary

  def print_score_diff_std_dev(self):
    """Print standard deviation of score differences"""
    print "class,std.dev"
    for cls in self.classes:
      print "%s,%0.5f" % (cls, np.std(self.scoresDiff[cls]))

  def print_score_diff_histogram(self, numOfBins):
    """Print histogram of score differences"""
    print "class,diff_upperbound,patch_count"
    for cls in self.classes:
      diffUpperbound = 0
      for i in range(0, numOfBins):
        count = 0
        for scoreDiff in self.scoresDiff[cls]:
          if (scoreDiff >= diffUpperbound) and (scoreDiff < (diffUpperbound + 1.0/numOfBins)):
            count += 1
        diffUpperbound += 1.0/numOfBins
        print "%s,%0.2f,%d" % (cls, diffUpperbound, count)

  def print_class_corrs(self):
    """Print all class correlations"""
    print "class, correlation"
    for cls in self.classes:
      corr = np.corrcoef(self.folder1Scores[cls], self.folder2Scores[cls])
      print "%s,%0.5f" % (cls, corr[0][1])

  def get_class_ids(self):
    """Get all class ids"""
    return self.classes

