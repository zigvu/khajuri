import logging, json, os

from postprocessing.task.Task import Task

from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect


class JsonReader(Task):

  def getVideoId(self, jsonFileName):
    baseName = os.path.basename(jsonFileName)
    return baseName.split('_')[0]

  def __call__(self, obj):
    fileName = obj
    logging.info('Reading frameInfo from %s' % fileName)
    if not self.config.videoId:
      self.config.videoId = self.getVideoId(fileName)
    jsonObj = json.load(open(fileName, 'r'))
    frame = Frame(
        self.config.ci_allClassIds, 543, self.config.ci_scoreTypes.keys())
    frame.frameDisplayTime = jsonObj['frame_time']
    frame.frameNumber = jsonObj['frame_number']
    frame.filename = None

    # Patch Scores
    for classId, scores in jsonObj['scores'].iteritems():
      for scoreType, scores in scores.iteritems():
        frame.addScore(classId, self.config.ci_scoreTypes[scoreType], 0, scores)

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
          logging.info('Adding localization %s' % loc)
          frame.addLocalization(classId, loc)

    return (frame, jsonObj['scores'].keys())
