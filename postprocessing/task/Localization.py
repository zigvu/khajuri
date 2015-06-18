import logging

from postprocessing.task.Task import Task

from Logo.PipelineMath.FramePostProcessor import FramePostProcessor


class Localization(Task):

  def __call__(self, obj):
    frame, classIds = obj
    for zDistThreshold in self.config.pp_zDistThresholds:
      for classId in classIds:
        logging.info(
            'Localize on %s for class %s at zDist: %s' %
            (frame, classId, zDistThreshold))
        frameLocalizer = FramePostProcessor(
            classId, self.config, frame, zDistThreshold)
        frameLocalizer.localize()

    return (frame, classIds)
