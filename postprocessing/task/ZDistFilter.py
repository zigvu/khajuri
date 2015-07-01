import numpy as np

from postprocessing.task.Task import Task


class ZDistFilter(Task):
  def __init__(self, config, status):
    Task.__init__(self, config, status)
    self.caffeInputCfg = self.config.caffeInput
    self.postProcessingCfg = self.config.postProcessing

  def __call__(self, obj):
    frame, classIds = obj
    # self.logger.debug('Starting ZDist on %s for classes %s' % (frame, classIds))
    for zDistThreshold in self.postProcessingCfg.pp_zDistThresholds[1:]:
      frame.scores[zDistThreshold] = frame.initNumpyArrayScore()
    self.zDistScore(frame, zDistThreshold)
    return (frame, classIds)

  def zDistScore(self, frame, zDistThreshold):
    for i in range(len(frame.scores[0][:, :, 1])):
      fc8scoresForPatch = frame.scores[0][i, :, 1]
      assert len(fc8scoresForPatch) == len(self.caffeInputCfg.ci_allClassIds)
      sortedScores = sorted(fc8scoresForPatch)[-5:]
      zDist = np.std(sortedScores) - np.std(sortedScores[-1:])
      # self.logger.debug('zDist is %s from scores %s' % (zDist, sortedScores))
      for zDistThreshold in self.postProcessingCfg.pp_zDistThresholds[1:]:
        if zDist >= zDistThreshold:
          frame.scores[zDistThreshold][i, :, 0] = frame.scores[0][i, :, 0]
