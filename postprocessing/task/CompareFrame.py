import logging

from postprocessing.task.Task import Task


class CompareFrame(Task):

  def __call__(self, obj):
    frame1, frame2 = obj
    logging.info('Comparing frame1 %s and frame2 %s.' % (frame1, frame2))
    scoreDiff = frame1.getScoreDiff(frame2)
    localizationDiff = frame1.getLocalizationDiff(frame2)
    logging.info('Score diff: %s' % scoreDiff)
    logging.info('Localization diff: %s' % localizationDiff)
    return (frame1, scoreDiff, localizationDiff)
