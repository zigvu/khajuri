import json, os

from postprocessing.task.Task import Task

from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect


class JsonReader(Task):
  def __init__(self, config, status):
    Task.__init__(self, config, status)
    self.slidingWindowCfg = self.config.slidingWindow
    self.caffeInputCfg = self.config.caffeInput

  def __call__(self, obj):
    fileName = obj
    self.logger.debug('JsonReader: %s' % fileName)
    jsonObj = json.load(open(fileName, 'r'))
    frame = Frame(
        self.caffeInputCfg.ci_allClassIds, 
        self.slidingWindowCfg.numOfSlidingWindows, 
        self.caffeInputCfg.ci_scoreTypes.keys()
    )
    frame.frameDisplayTime = jsonObj['frame_time']
    frame.frameNumber = jsonObj['frame_number']
    frame.filename = None

    # Patch Scores
    for classId, scores in jsonObj['scores'].iteritems():
      for scoreType, scores in scores.iteritems():
        frame.addScore(
            classId, self.caffeInputCfg.ci_scoreTypes[scoreType], 0, scores)

    # Localizations
    if jsonObj.get('localizations'):
      for classId, localizationList in jsonObj['localizations'].iteritems():
        for loc in localizationList:
          score = loc['score']
          scale = loc['scale']
          bbox = loc['bbox']
          zDist = loc['zdist_thresh']
          rect = Rect(bbox['x'], bbox['y'], bbox['width'], bbox['height'])
          loc = Localization(zDist, classId, rect, score, scale)
          # self.logger.debug('Adding localization %s' % loc)
          frame.addLocalization(classId, loc)

    return (frame, jsonObj['scores'].keys())
