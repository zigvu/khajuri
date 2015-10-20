from Logo.PipelineMath.PeaksExtractor import PeaksExtractor
from Logo.PipelineMath.PixelMapper import PixelMapper

from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect


class FramePostProcessor(object):
  """Create localizations for a particular class"""

  def __init__(self, classId, config, frame, zDistThreshold):
    """Initialize values"""
    self.classId = classId
    self.config = config
    self.slidingWindowCfg = self.config.slidingWindow
    self.logger = self.config.logging.logger
    self.frame = frame
    self.zDistThreshold = zDistThreshold

  def localize(self):
    """Collect and analyze detection results"""
    pixelMapper = PixelMapper(
      self.classId, self.config, self.frame, self.zDistThreshold)
    # get localizations for all scales
    for lclzOrigScale in self.slidingWindowCfg.sw_scales:
      lclzPixelMap = pixelMapper.getLocalizationMap(lclzOrigScale)
      lclzPixelMap.setScale(1.0)
      lclzPeaks = PeaksExtractor(lclzPixelMap, self.config)
      lclzPatches = lclzPeaks.getPeakBboxes()
      for lp in lclzPatches:
        # self.logger.debug(
        #     'Localization at: %s, with intensity: %s for class %s and zDist %s' %
        #     (lp['bbox'].json_format(), lp['intensity'], self.classId,
        #      self.zDistThreshold))
        rect = Rect(
            lp['bbox'].x0, lp['bbox'].y0, lp['bbox'].width, lp['bbox'].height)
        loc = Localization(
            self.zDistThreshold, self.classId, rect, lp['intensity'],
            lclzOrigScale)
        self.frame.addLocalization(self.classId, loc)
