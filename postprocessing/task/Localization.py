from postprocessing.task.Task import Task

from Logo.PipelineMath.FramePostProcessor import FramePostProcessor


class Localization(Task):
  def __init__(self, config, status):
    Task.__init__(self, config, status)
    self.postProcessingCfg = self.config.postProcessing

  def __call__(self, obj):
    frame, classIds = obj
    for zDistThreshold in self.postProcessingCfg.pp_zDistThresholds:
      for classId in classIds:
        # self.logger.debug(
        #     'Localize on %s for class %s at zDist: %s' %
        #     (frame, classId, zDistThreshold))
        frameLocalizer = FramePostProcessor(
            classId, self.config, frame, zDistThreshold)
        frameLocalizer.localize()

    return (frame, classIds)
