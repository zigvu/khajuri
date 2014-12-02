import sys, os, glob
import logging
from collections import OrderedDict

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter

class JSONFileComparer( object ):
  def __init__( self, jsonFileName1, jsonFileName2 ):
    """Initialize"""
    self.jrw1 = JSONReaderWriter(jsonFileName1)
    self.jrw2 = JSONReaderWriter(jsonFileName2)

  def get_class_ids(self):
    """Get all class ids"""
    return self.jrw1.getClassIds()

  def get_diff_patch_scores(self, verbose_print=False):
    """Get max, avg, min of patch scores in files"""
    # store differences
    diffMax = OrderedDict()
    diffMin = OrderedDict()
    diffAvg = OrderedDict()
    counter = 0
    for cls in self.jrw1.getClassIds():
      diffMax[cls] = -1
      diffAvg[cls] = 0
      diffMin[cls] = 999

    # loop through all scales 
    if verbose_print:
      print "patchFileName,class,jsonScore1,jsonScore2"
    for scale in self.jrw1.getScalingFactors():
      for patch1 in self.jrw1.getPatches(scale):
        patchFileName = patch1['patch_filename']

        # for second json
        for patch2 in self.jrw2.getPatches(scale):
          if patchFileName == patch2['patch_filename']:
            # compare scores
            for cls in self.jrw1.getClassIds():
              jsonScore1 = patch1['scores'][cls]
              jsonScore2 = patch2['scores'][cls]
              diff = jsonScore1 - jsonScore2
              diffMax[cls] = max(diff, diffMax[cls])
              diffAvg[cls] = diff + diffAvg[cls]
              diffMin[cls] = min(diff, diffMin[cls])
              counter += 1
              if verbose_print:
                if abs(diff) > 0.01:
                  print "%s, %s, %0.4f, %0.4f, <---" % (patchFileName, cls, jsonScore1, jsonScore2)
                else:
                  print "%s, %s, %0.4f, %0.4f" % (patchFileName, cls, jsonScore1, jsonScore2)
    # convert avg
    for cls in self.jrw1.getClassIds():
      diffAvg[cls] = diffAvg[cls]/counter
    # return
    return diffMax, diffAvg, diffMin
