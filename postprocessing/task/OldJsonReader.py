import json
import numpy as np
import os

from postprocessing.task.Task import Task

from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect


class OldJsonReader(Task):
  def __init__(self, config, status):
    Task.__init__(self, config, status)
    self.slidingWindowCfg = self.config.slidingWindow
    self.caffeInputCfg = self.config.caffeInput
    self.allCellBoundariesDict = self.config.allCellBoundariesDict


  def getPatches(self, scale):
    # Patch Scores
    for obj in self.myDict['scales']:
      if obj['scale'] == scale:
        return obj['patches']

  def getClassIds(self):
    classIds = self.myDict['scales'][0]['patches'][0]['scores'].keys()
    return classIds

  def __call__(self, obj):
    fileName = obj
    self.logger.debug('OldJsonReader: %s' % fileName)
    self.myDict = json.load(open(fileName, 'r'))
    frame = Frame(
        self.caffeInputCfg.ci_allClassIds, 
        self.slidingWindowCfg.numOfSlidingWindows, 
        self.caffeInputCfg.ci_scoreTypes.keys()
    )
    frame.frameNumber = self.myDict["frame_number"]
    self.patchMapping = self.allCellBoundariesDict["patchMapping"]
    self.classIds = self.getClassIds()
    scores = np.zeros((len(self.patchMapping.keys()), len(self.classIds)))
    fc8scores = np.zeros((len(self.patchMapping.keys()), len(self.classIds)))
    for scale in self.slidingWindowCfg.sw_scales:
      for patch in self.getPatches(scale):
        x = patch["patch"]["x"]
        y = patch["patch"]["y"]
        w = patch["patch"]["width"]
        h = patch["patch"]["height"]
        patchId = self.patchMapping[(scale, x, y, x + w, y + h)]
        for classId in self.classIds:
          scores[patchId, classId] = patch["scores"][classId]
          if patch.get("scores_fc8"):
            fc8scores[patchId, classId] = patch["scores_fc8"][classId]

    frame.scores[0][:, :, 0] = scores
    frame.scores[0][:, :, 1] = fc8scores

    # self.logger.debug('Reading localizations from file %s' % fileName)
    if self.myDict.get('localizations'):
      for classId in self.classIds:
        lList = self.myDict['localizations'].get(classId)
        for lDict in lList:
          # self.logger.debug('Got the localization dict %s' % lDict)
          rect = Rect(
              lDict["bbox"]["x"], lDict["bbox"]["y"], lDict["bbox"]["width"],
              lDict["bbox"]["height"])
          loc = Localization(0, classId, rect, lDict["score"], 1)
          # self.logger.debug(
          #     'Adding localization %s to frame from file %s' % (loc, fileName))
          frame.addLocalization(int(classId), loc)
    else:
      # self.logger.debug('Localization is not present in file %s' % fileName)
      pass
    return (frame, self.classIds)
