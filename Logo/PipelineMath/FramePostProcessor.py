import logging

from Logo.PipelineMath.ScaleSpaceCombiner import ScaleSpaceCombiner
from Logo.PipelineMath.PeaksExtractor import PeaksExtractor

from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect


class FramePostProcessor(object):
  """Create localizations for a particular class"""

  def __init__(self, classId, config, frame, zDistThreshold):
    """Initialize values"""
    self.classId = classId
    self.config = config
    self.frame = frame
    self.zDistThreshold = zDistThreshold

  def localize(self):
    """Collect and analyze detection results"""
    scaleSpaceCombiner = ScaleSpaceCombiner(
        self.classId, self.config, self.frame, self.zDistThreshold)
    lclzOrigScale, lclzPixelMap = scaleSpaceCombiner.getBestInferredPixelMap()
    lclzPixelMap.setScale(1.0)
    lclzPeaks = PeaksExtractor(lclzPixelMap, self.config)
    lclzPatches = lclzPeaks.getPeakBboxes()
    for lp in lclzPatches:
      logging.info(
          'Localization at: %s, with intensity: %s for class %s and zDist %s' %
          (lp['bbox'].json_format(), lp['intensity'], self.classId,
           self.zDistThreshold))
      rect = Rect(
          lp['bbox'].x0, lp['bbox'].y0, lp['bbox'].width, lp['bbox'].height)
      l = Localization(
          self.zDistThreshold, self.classId, rect, lp['intensity'],
          lclzOrigScale)
      self.frame.addLocalization(self.classId, l)
    return lclzPatches
