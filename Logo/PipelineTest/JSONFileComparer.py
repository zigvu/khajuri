import sys, os, glob, math
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

  def get_diff_post_processing(self, method, verbose_print=False):
    """Get max of curation bboxes and scores in files"""
    if verbose_print:
      print "\n%s differences" % method
    # store differences - all are max
    diffNumBboxes = OrderedDict()
    diffXPosOfBboxes = OrderedDict()
    diffYPosOfBboxes = OrderedDict()
    diffAreaOfBboxes = OrderedDict()
    diffScoreOfBboxes = OrderedDict()
    for cls in self.jrw1.getClassIds():
      diffNumBboxes[cls] = 0
      diffXPosOfBboxes[cls] = 0
      diffYPosOfBboxes[cls] = 0
      diffAreaOfBboxes[cls] = 0
      diffScoreOfBboxes[cls] = -1

    # loop through all scales 
    if verbose_print:
      print "cls,bboxCountDiff,x1,y1,width1,height1,x2,y2,width2,height2,scoreDiff"
    for cls in self.jrw1.getClassIds():
      # sort bboxes by x-axis values
      jrw1Boxes = None
      jrw2Boxes = None
      if method == "localization":
        jrw1Boxes = sorted(self.jrw1.getLocalizations(cls), key = lambda bbox: bbox['bbox']['x'])
        jrw2Boxes = sorted(self.jrw2.getLocalizations(cls), key = lambda bbox: bbox['bbox']['x'])
      elif method == "curation":
        jrw1Boxes = sorted(self.jrw1.getCurations(cls), key = lambda bbox: bbox['bbox']['x'])
        jrw2Boxes = sorted(self.jrw2.getCurations(cls), key = lambda bbox: bbox['bbox']['x'])
      else:
        raise RuntimeError("Unknown post-processing method")

      diffNumBBox = abs(len(jrw1Boxes) - len(jrw2Boxes))
      diffNumBboxes[cls] = max(diffNumBBox, diffNumBboxes[cls])

      if diffNumBBox <= 0:
        for jrw1Box in jrw1Boxes:
          # get the bounding box with the closest center to this bounding box
          minDiff = 999999
          minjrw2Box = None
          for jrw2Box in jrw2Boxes:
            xCenter1 = abs(jrw1Box['bbox']['x'] + jrw1Box['bbox']['width']/2)
            xCenter2 = abs(jrw2Box['bbox']['x'] + jrw2Box['bbox']['width']/2)
            yCenter1 = abs(jrw1Box['bbox']['y'] + jrw1Box['bbox']['height']/2)
            yCenter2 = abs(jrw2Box['bbox']['y'] + jrw2Box['bbox']['height']/2)

            centerDiff = math.sqrt((xCenter1 - xCenter2)**2 + (yCenter1 - yCenter2)**2)
            if centerDiff < minDiff:
              minjrw2Box = jrw2Box
              minDiff = centerDiff
          # if we found the closest
          if minjrw2Box != None:
            # remove from list
            jrw2Boxes = [x for x in jrw2Boxes if x != minjrw2Box]
            # get storage values
            xDiff = abs(jrw1Box['bbox']['x'] - minjrw2Box['bbox']['x'])
            yDiff = abs(jrw1Box['bbox']['y'] - minjrw2Box['bbox']['y'])
            wDiff = abs(jrw1Box['bbox']['width'] - minjrw2Box['bbox']['width'])
            hDiff = abs(jrw1Box['bbox']['height'] - minjrw2Box['bbox']['height'])
            scoreDiff = abs(jrw1Box['score'] - minjrw2Box['score'])

            diffXPosOfBboxes[cls] = max(xDiff, diffXPosOfBboxes[cls])
            diffYPosOfBboxes[cls] = max(yDiff, diffYPosOfBboxes[cls])
            diffAreaOfBboxes[cls] = max(wDiff * hDiff, diffAreaOfBboxes[cls])
            diffScoreOfBboxes[cls] = max(scoreDiff, diffScoreOfBboxes[cls])

            if verbose_print:
              if scoreDiff > 0.01:
                print "%s, %d, %d, %d, %d, %d, %d, %d, %d, %d, %0.4f <---" % (
                  cls, 0,
                  jrw1Box['bbox']['x'], jrw1Box['bbox']['y'], 
                  jrw1Box['bbox']['width'], jrw1Box['bbox']['height'], 
                  jrw2Box['bbox']['x'], jrw2Box['bbox']['y'], 
                  jrw2Box['bbox']['width'], jrw2Box['bbox']['height'], scoreDiff)
              else:
                print "%s, %d, %d, %d, %d, %d, %d, %d, %d, %d, %0.4f" % (
                  cls, 0,
                  jrw1Box['bbox']['x'], jrw1Box['bbox']['y'], 
                  jrw1Box['bbox']['width'], jrw1Box['bbox']['height'], 
                  jrw2Box['bbox']['x'], jrw2Box['bbox']['y'], 
                  jrw2Box['bbox']['width'], jrw2Box['bbox']['height'], scoreDiff)
      # more than 1 localization box
      else:
        if verbose_print:
          print "%s, %d, -1, -1, -1, -1, -1, -1, -1, -1, -1 <---" % (cls, diffNumBBox)

    # return
    return diffNumBboxes, diffXPosOfBboxes, diffYPosOfBboxes, diffAreaOfBboxes, diffScoreOfBboxes

  def get_diff_patch_scores(self, verbose_print=False):
    """Get max, avg, min of patch scores in files"""
    if verbose_print:
      print "\nPatch score differences"
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
