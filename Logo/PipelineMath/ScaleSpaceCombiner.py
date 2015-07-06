import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.PixelMapper import PixelMapper
import matplotlib.pyplot as plt


class ScaleSpaceCombiner(object):
  """Combine detection across scales"""

  def __init__(self, classId, config, frame, zDistThreshold):
    """Initialize class"""
    self.classId = classId
    self.config = config
    self.frame = frame
    self.zDistThreshold = zDistThreshold
    self.pixelMapper = PixelMapper(classId, config, frame, self.zDistThreshold)
    scaleDecayFactors = self.config.sw_scale_decay_factors
    self.pixelMapper.setupScaleDecayedMapCache(scaleDecayFactors)

  def getBestInferredPixelMap(self):
    """Get the Best Localization Map"""
    maxLocalizationScale = self.config.sw_scales[0]
    maxLocalizationMap = self.pixelMapper.getScaleDecayedMap(
        maxLocalizationScale)
    maxPixelLocalization = 1E-10
    for scale in self.config.sw_scales:
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
    #plt.imshow(
    #    rescaledLocalizationMap.toNumpyArray() ).write_png( '/tmp/output/final_localization_%s_%s_%s.png'
    #        % ( self.frame.frameNumber, self.classId, self.zDistThreshold ) )
    return maxLocalizationScale, rescaledLocalizationMap
