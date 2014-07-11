import math
import numpy as np

from PixelMapper import PixelMapper
from Rectangle import Rectangle

class ScaleSpaceCombiner(object):
  def __init__(self, staticBoundingBoxes, jsonReaderWriter):
    """Initialize class"""
    self.pixelMapper = PixelMapper(staticBoundingBoxes, jsonReaderWriter)
    # infer scaling factors
    self.allScalingFactors = None
    self.originalScalingFactors = np.unique(np.sort(jsonReaderWriter.getScalingFactors()).copy())
    self.classIds = jsonReaderWriter.getClassIds()
    self.allScalingFactors, self.inferredScalingFactors = self.getAllScalingFactors()

  def getBestInferredPixelMap(self, classId):
    """From among the inferred scales, select best pixelMap based on 
    (a) localization and then (b) rescaled by intensity at the highest localization
    Returns pixelMap"""
    # first, find best localization
    maxLocalizationScale = self.inferredScalingFactors[0]
    maxLocalizationMap = self.pixelMapper.getLocalizationMap(classId, maxLocalizationScale)
    maxPixelLocalization = 1E-10
    for inferredScale in self.inferredScalingFactors:
      curLocalizationMap = self.pixelMapper.getLocalizationMap(classId, inferredScale)
      curMaxPixelValue = np.max(curLocalizationMap)
      if curMaxPixelValue > maxPixelLocalization:
        maxPixelLocalization = curMaxPixelValue
        maxLocalizationScale = inferredScale
        maxLocalizationMap = curLocalizationMap
    localizationPixelMask = maxLocalizationMap >= maxPixelLocalization
    # now, re-calculate intensity
    intensityAtScale = self.pixelMapper.getIntensityMap(classId, maxLocalizationScale)
    maxPixelIntensity = np.max(intensityAtScale * localizationPixelMask)
    rescalingFactor = maxPixelIntensity / maxPixelLocalization
    rescaledLocalizationMap = maxLocalizationMap * rescalingFactor
    return rescaledLocalizationMap

  def getBestIntensityPixelMap(self, classId):
    """From among all scales, select pixelMap with highest intensity
    Returns pixelMap"""
    maxIntensityScale = self.allScalingFactors[0]
    maxIntensityMap = self.pixelMapper.getIntensityMap(classId, maxIntensityScale)
    maxPixelIntensity = 1E-10
    for scale in self.allScalingFactors:
      curIntensityMap = self.pixelMapper.getIntensityMap(classId, scale)
      curMaxPixelValue = np.max(curIntensityMap)
      if curMaxPixelValue > maxPixelIntensity:
        maxPixelIntensity = curMaxPixelValue
        maxIntensityScale = scale
        maxIntensityMap = curIntensityMap
    return maxIntensityMap

  def getAllScalingFactors(self):
    """Infer intermediate scaling factors that are averages between two
    consecutive scaling factors from config"""
    if self.allScalingFactors != None:
      return self.allScalingFactors
    # infer intermediate scales
    inferredScalingFactors = []
    for idx, scl in enumerate(self.originalScalingFactors):
      if idx == (len(self.originalScalingFactors) - 1):
        break
      for classId in self.classIds:
        scale1 = round(self.originalScalingFactors[idx], 1)
        scale2 = round(self.originalScalingFactors[idx + 1], 1)
        scale = round((scale1 + scale2)/2, 1)
        inferredScalingFactors = np.unique(np.append(inferredScalingFactors, [scale]))
        self.pixelMapper.inferIntermediateScales(classId, scale, scale1, scale2)
    allScalingFactors = np.unique(np.append(inferredScalingFactors, self.originalScalingFactors))
    return allScalingFactors, inferredScalingFactors
