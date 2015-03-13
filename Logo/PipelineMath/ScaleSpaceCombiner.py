import math
import numpy as np

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.PixelMapper import PixelMapper

class ScaleSpaceCombiner(object):
  def __init__(self, classId, staticBoundingBoxes, jsonReaderWriter, allCellBoundariesDict):
    """Initialize class"""
    self.classId = classId
    self.pixelMapper = PixelMapper(classId, staticBoundingBoxes, jsonReaderWriter, allCellBoundariesDict)
    # infer scaling factors
    self.allScalingFactors = None
    self.originalScalingFactors = np.unique(np.sort(jsonReaderWriter.getScalingFactors()).copy())
    self.allScalingFactors, self.inferredScalingFactors = self.getAllScalingFactors()
    # decay scores across scales
    # TODO: move to config
    scaleDecayFactors = self.getScaledDecayFactors()
    self.pixelMapper.setupScaleDecayedMapCache(scaleDecayFactors)


  def getBestInferredPixelMap(self):
    """From among the inferred scales, select best pixelMap based on 
    (a) localization and then (b) rescaled by intensity at the highest localization
    Returns pixelMap"""
    # first, find best localization
    maxLocalizationScale = self.originalScalingFactors[0]
    maxLocalizationMap = self.pixelMapper.getScaleDecayedMap(maxLocalizationScale)
    maxPixelLocalization = 1E-10
    for scale in self.originalScalingFactors:
      curLocalizationMap = self.pixelMapper.getScaleDecayedMap(scale)
      curMaxPixelValue = np.max(curLocalizationMap.cellValues)
      if curMaxPixelValue > maxPixelLocalization:
        maxPixelLocalization = curMaxPixelValue
        maxLocalizationScale = scale
        maxLocalizationMap = curLocalizationMap
    localizationPixelMask = maxLocalizationMap.cellValues >= maxPixelLocalization
    # now, re-calculate intensity
    intensityAtScale = self.pixelMapper.getIntensityMap(maxLocalizationScale)
    maxPixelIntensity = np.max(intensityAtScale.cellValues * localizationPixelMask)
    rescalingFactor = maxPixelIntensity / maxPixelLocalization
    rescaledLocalizationMap = maxLocalizationMap.copy()
    rescaledLocalizationMap.cellValues = maxLocalizationMap.cellValues * rescalingFactor
    return rescaledLocalizationMap


  def getBestInferredPixelMap_old(self):
    """From among the inferred scales, select best pixelMap based on 
    (a) localization and then (b) rescaled by intensity at the highest localization
    Returns pixelMap"""
    # first, find best localization
    maxLocalizationScale = self.inferredScalingFactors[0]
    maxLocalizationMap = self.pixelMapper.getLocalizationMap(maxLocalizationScale)
    maxPixelLocalization = 1E-10
    for inferredScale in self.inferredScalingFactors:
      curLocalizationMap = self.pixelMapper.getLocalizationMap(inferredScale)
      curMaxPixelValue = np.max(curLocalizationMap.cellValues)
      if curMaxPixelValue > maxPixelLocalization:
        maxPixelLocalization = curMaxPixelValue
        maxLocalizationScale = inferredScale
        maxLocalizationMap = curLocalizationMap
    localizationPixelMask = maxLocalizationMap.cellValues >= maxPixelLocalization
    # now, re-calculate intensity
    intensityAtScale = self.pixelMapper.getIntensityMap(maxLocalizationScale)
    maxPixelIntensity = np.max(intensityAtScale.cellValues * localizationPixelMask)
    rescalingFactor = maxPixelIntensity / maxPixelLocalization
    rescaledLocalizationMap = maxLocalizationMap.copy()
    rescaledLocalizationMap.cellValues = maxLocalizationMap.cellValues * rescalingFactor
    return rescaledLocalizationMap

  def getBestIntensityPixelMap(self):
    """From among all scales, select pixelMap with highest intensity
    Returns pixelMap"""
    maxIntensityScale = self.allScalingFactors[0]
    maxIntensityMap = self.pixelMapper.getIntensityMap(maxIntensityScale)
    maxPixelIntensity = 1E-10
    for scale in self.allScalingFactors:
      curIntensityMap = self.pixelMapper.getIntensityMap(scale)
      curMaxPixelValue = np.max(curIntensityMap.cellValues)
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
      scale1 = round(self.originalScalingFactors[idx], 1)
      scale2 = round(self.originalScalingFactors[idx + 1], 1)
      scale = round((scale1 + scale2)/2, 1)
      inferredScalingFactors = np.unique(np.append(inferredScalingFactors, [scale]))
      self.pixelMapper.inferIntermediateScales(scale, scale1, scale2)
    allScalingFactors = np.unique(np.append(inferredScalingFactors, self.originalScalingFactors))
    return allScalingFactors, inferredScalingFactors

  def getScaledDecayFactors(self):
    """TODO: Put in config"""
    # TODO
    scaleDecayFactors = [
      {
        'scale': 0.4,
        'factors': [{'scale': 0.4, 'factor': 0.8},
                {'scale': 0.7, 'factor': 0.15},
                {'scale': 1.0, 'factor': 0.05},
                {'scale': 1.3, 'factor': 0},
                {'scale': 1.6, 'factor': 0}]
      },
      {
        'scale': 0.7,
        'factors': [{'scale': 0.4, 'factor': 0.1},
                {'scale': 0.7, 'factor': 0.8},
                {'scale': 1.0, 'factor': 0.1},
                {'scale': 1.3, 'factor': 0},
                {'scale': 1.6, 'factor': 0}]
      },
      {
        'scale': 1.0,
        'factors': [{'scale': 0.4, 'factor': 0},
                {'scale': 0.7, 'factor': 0.1},
                {'scale': 1.0, 'factor': 0.8},
                {'scale': 1.3, 'factor': 0.1},
                {'scale': 1.6, 'factor': 0}]
      },
      {
        'scale': 1.3,
        'factors': [{'scale': 0.4, 'factor': 0},
                {'scale': 0.7, 'factor': 0},
                {'scale': 1.0, 'factor': 0.1},
                {'scale': 1.3, 'factor': 0.8},
                {'scale': 1.6, 'factor': 0.1}]
      },
      {
        'scale': 1.6,
        'factors': [{'scale': 0.4, 'factor': 0},
                {'scale': 0.7, 'factor': 0},
                {'scale': 1.0, 'factor': 0.05},
                {'scale': 1.3, 'factor': 0.15},
                {'scale': 1.6, 'factor': 0.8}]
      }]
    return scaleDecayFactors
