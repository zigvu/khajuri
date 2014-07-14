import math
import numpy as np
import scipy.ndimage as ndimage
from skimage.transform import resize

class PixelMapper(object):
  def __init__(self, staticBoundingBoxes, jsonReaderWriter):
    """Initialize pixelMap according to dimensions of image and sliding window"""
    self.staticBoundingBoxes = staticBoundingBoxes
    self.origImageShape = (staticBoundingBoxes.imageDim.height, staticBoundingBoxes.imageDim.width)
    self.jsonReaderWriter = jsonReaderWriter
    self.pixelMaps = []
    for classId in jsonReaderWriter.getClassIds():
      for scale in jsonReaderWriter.getScalingFactors():
        localizationMap, intensityMap = self.populatePixelMap(classId, scale)
        self.pixelMaps += [{'classId': classId, 'scale': scale, \
          'localizationMap': localizationMap, 'intensityMap': intensityMap}]

  def populatePixelMap(self, classId, scale):
    """Initialize the pixel map for the class at given scale"""
    rescoringMap = self.staticBoundingBoxes.pixelMapToRemoveDoubleCounting(scale)
    localizationMap = np.zeros(np.shape(rescoringMap))
    intensityMap = np.zeros(np.shape(rescoringMap))
    for patch in self.jsonReaderWriter.getPatches(scale):
      rStart = patch['patch']['y']
      rEnd = patch['patch']['y'] + patch['patch']['height']
      cStart = patch['patch']['x']
      cEnd = patch['patch']['x'] + patch['patch']['width']
      patchScore = float(patch['scores'][classId])
      # localization uses averaging
      localizationMap[rStart:rEnd, cStart:cEnd] += patchScore
      # intensity uses max pooling
      intensityScoreMask = intensityMap[rStart:rEnd, cStart:cEnd] < patchScore
      intensityMap[rStart:rEnd, cStart:cEnd][intensityScoreMask] = patchScore
    # localization needs rescoring to get rid of double counting artifacts
    localizationMapZoomed = resize(localizationMap * rescoringMap, self.origImageShape, order=0)
    intensityMapZoomed = resize(intensityMap, self.origImageShape, order=0)
    # TODO: convolution will be required when doing temporal combination
    # convolutedMap = ndimage.gaussian_filter(reScoredPixelMap, round(16/scale))
    return localizationMapZoomed, intensityMapZoomed

  def inferIntermediateScales(self, classId, targetScale, scale1, scale2):
    """Given pixelMap at two scales, infer localization of itermediate scale for classId"""
    # localization
    localization1 = self.getLocalizationMap(classId, scale1)
    localization2 = self.getLocalizationMap(classId, scale2)
    avgLocalization = (localization1 + localization2) / 2
    # intensity
    intensity1 = self.getIntensityMap(classId, scale1)
    intensity2 = self.getIntensityMap(classId, scale2)
    avgIntensity = (intensity1 + intensity2) / 2
    self.pixelMaps += [{'classId': classId, 'scale': targetScale, \
      'localizationMap': avgLocalization, 'intensityMap': avgIntensity}]

  def getLocalizationMap(self, classId, scale):
    """Return the localization map for this class and scale"""
    for pm in self.pixelMaps:
      if (pm['classId'] == classId) and (pm['scale'] == scale):
        return pm['localizationMap']
    return None    

  def getIntensityMap(self, classId, scale):
    """Return the intensity map for this class and scale"""
    for pm in self.pixelMaps:
      if (pm['classId'] == classId) and (pm['scale'] == scale):
        return pm['intensityMap']
    return None    
