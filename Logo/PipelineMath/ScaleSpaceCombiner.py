import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.PixelMapper import PixelMapper
from Logo.PipelineMath.PixelMap import PixelMap
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

  def getBestInferredPixelMap1(self):
    """Get the Best Localization Map"""
    combinedLocalizationMap =  PixelMap(
        self.config.allCellBoundariesDict, self.config.neighborMap, 1.0)
    for scale in self.config.sw_scales:
      localizationAtScale = self.pixelMapper.getLocalizationMap(scale)
      combinedLocalizationMap.cellValues += localizationAtScale.cellValues
      combinedLocalizationMap.cellValues /= 2
    #plt.imshow(
    #    combinedLocalizationMap.toNumpyArray() ).write_png( 'final_localization_%s_%s_%s.png'
    #        % ( self.frame.frameNumber, self.classId, self.zDistThreshold ) )
    return 1.0, combinedLocalizationMap

  def getBestInferredPixelMap(self):
    """Get the Best Localization Map"""
    maxLocalizationScale = self.config.sw_scales[0]
    maxLocalizationMap = self.pixelMapper.getScaleDecayedMap( maxLocalizationScale)
    maxPixelLocalization = 1E-1000
    for scale in self.config.sw_scales:
      curLocalizationMap = self.pixelMapper.getScaleDecayedMap(scale)
      curMaxPixelValue = np.max(curLocalizationMap.cellValues) * scale
      #if curMaxPixelValue > self.config.pp_detectorThreshold and scale > maxLocalizationScale:
      if curMaxPixelValue > maxPixelLocalization:
        maxPixelLocalization =  np.max(curLocalizationMap.cellValues) 
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
    #    rescaledLocalizationMap.toNumpyArray() ).write_png( 'final_localization_%s_%s_%s.png'
    #        % ( self.frame.frameNumber, self.classId, self.zDistThreshold ) )
    return maxLocalizationScale, rescaledLocalizationMap
  
