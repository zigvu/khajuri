import numpy as np

from Logo.PipelineMath.PixelMapper import PixelMapper


class ScaleSpaceCombiner(object):
  """Combine detection across scales"""

  def __init__(self, classId, config, frame, zDistThreshold):
    """Initialize class"""
    self.pixelMapper = PixelMapper(classId, config, frame, zDistThreshold)

    self.slidingWindowCfg = config.slidingWindow

    self.pixelMapper.setupScaleDecayedMapCache(
        self.slidingWindowCfg.sw_scale_decay_factors)

  def getBestInferredPixelMap(self):
    """Get the Best Localization Map"""
    maxLocalizationScale = self.slidingWindowCfg.sw_scales[0]
    maxLocalizationMap = self.pixelMapper.getScaleDecayedMap(
        maxLocalizationScale)
    maxPixelLocalization = 1E-10
    for scale in self.slidingWindowCfg.sw_scales:
      curLocalizationMap = self.pixelMapper.getScaleDecayedMap(scale)
      curMaxPixelValue = np.max(curLocalizationMap.cellValues)
      if curMaxPixelValue > maxPixelLocalization:
        maxPixelLocalization = curMaxPixelValue
        maxLocalizationScale = scale
        maxLocalizationMap = curLocalizationMap
    localizationPixelMask = maxLocalizationMap.cellValues >= maxPixelLocalization
    intensityAtScale = self.pixelMapper.getIntensityMap(maxLocalizationScale)
    maxPixelIntensity = np.max(
        intensityAtScale.cellValues * localizationPixelMask)
    rescalingFactor = maxPixelIntensity / maxPixelLocalization
    rescaledLocalizationMap = maxLocalizationMap.copy()
    rescaledLocalizationMap.cellValues = maxLocalizationMap.cellValues * rescalingFactor
    return maxLocalizationScale, rescaledLocalizationMap
