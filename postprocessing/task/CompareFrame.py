from postprocessing.task.Task import Task


class CompareFrame(Task):

  def __call__(self, obj):
    frame1, frame2 = obj
    self.logger.debug('Comparing frame1 %s and frame2 %s.' % (frame1, frame2))
    scoreDiff = frame1.getScoreDiff(frame2)
    localizationDiff = frame1.getLocalizationDiff(frame2)
    self.logger.debug('Score diff: %s' % scoreDiff)
    self.logger.debug('Localization diff: %s' % localizationDiff)
    return (frame1, scoreDiff, localizationDiff)
