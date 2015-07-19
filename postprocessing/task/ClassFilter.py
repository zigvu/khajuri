import numpy as np

from postprocessing.task.Task import Task


class ClassFilter(Task):

  def __init__(self, config, status):
    Task.__init__(self, config, status)
    self.caffeInputCfg = self.config.caffeInput
    self.postProcessingCfg = self.config.postProcessing

  def __call__(self, obj):
    frame, classIds = obj
    self.logger.debug(
        'Frame Number: %d, Classes: %s' % (frame.frameNumber, classIds))
    return self.splitUsingThreshold(frame, classIds, 0)

  def splitUsingThreshold(self, frame, classIds, zDist):
    threshold = self.postProcessingCfg.pp_detectorThreshold
    backgroundClassIds = self.caffeInputCfg.ci_backgroundClassIds

    maxArray = np.amax(frame.scores[zDist][:, :, 0], axis=0)

    above = set(np.argwhere(maxArray > threshold).flatten())
    # self.logger.debug(
    #     'Reduce list size from %s to %s' % (len(classIds), len(above)))
    above = above.difference(set(map(int, backgroundClassIds)))
    return (frame, above)
