import logging
import numpy as np

from postprocessing.task.Task import Task


class ClassFilter(Task):

  def __call__(self, obj):
    frame, classIds = obj
    logging.info(
        'Starting Class Filter on %s for classes %s' % (frame, classIds))
    return self.splitUsingThreshold(frame, classIds, 0)

  def splitUsingThreshold(self, frame, classIds, zDist):
    threshold = self.config.pp_detectorThreshold
    maxArray = np.amax(frame.scores[zDist][:, :, 0], axis=0)

    above = set(np.argwhere(maxArray > threshold).flatten())
    logging.info('Reduce list size from %s to %s' % (len(classIds), len(above)))
    above = above.difference(set(map(int, self.config.ci_backgroundClassIds)))
    return (frame, above)
