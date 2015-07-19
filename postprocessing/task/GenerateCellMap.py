from postprocessing.task.Task import Task

from Logo.PipelineMath.PixelMap import PixelMap


class GenerateCellMap(Task):

  def __call__(self, obj):
    scale, patchScores = obj
    self.logger.debug(
        'Starting patchScores to cellMap translation for patchScores %s at scale %s'
        % (patchScores, scale))
    pixelMap = PixelMap(self.config.allCellBoundariesDict, scale)
    pixelMap.addScore(patchScores)
    return pixelMap.cellValues
