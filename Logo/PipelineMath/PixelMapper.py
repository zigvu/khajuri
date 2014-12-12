import math
import numpy as np
import scipy.ndimage as ndimage
from skimage.transform import resize
from PixelMap import PixelMap

class PixelMapper(object):
  def __init__(self, classId, staticBoundingBoxes, jsonReaderWriter, allCellBoundariesDict ):
    """Initialize pixelMap according to dimensions of image and sliding window"""
    self.classId = classId
    self.staticBoundingBoxes = staticBoundingBoxes
    self.origImageShape = (staticBoundingBoxes.imageDim.height, staticBoundingBoxes.imageDim.width)
    self.jsonReaderWriter = jsonReaderWriter
    self.pixelMaps = []
    self.scales = jsonReaderWriter.getScalingFactors()
    self.allCellBoundariesDict = allCellBoundariesDict
    for scale in self.scales:
      localizationMap, intensityMap = self.populatePixelMap(scale)
      self.pixelMaps += [{'scale': scale, \
        'localizationMap': localizationMap, 'intensityMap': intensityMap}]

  def populatePixelMap(self, scale):
    """Initialize the pixel map for the class at given scale"""
    rescoringMap = PixelMap( self.allCellBoundariesDict, scale )
    localizationMap = PixelMap( self.allCellBoundariesDict, scale )
    intensityMap = PixelMap( self.allCellBoundariesDict, scale )
    for patch in self.jsonReaderWriter.getPatches(scale):
      rStart = patch['patch']['y']
      rEnd = patch['patch']['y'] + patch['patch']['height']
      cStart = patch['patch']['x']
      cEnd = patch['patch']['x'] + patch['patch']['width']
      patchScore = float(patch['scores'][self.classId])
      # rescoring uses addition
      rescoringMap.addScore( cStart, rStart, cEnd, rEnd, 1 ) 
      # localization uses averaging
      localizationMap.addScore( cStart, rStart, cEnd, rEnd, patchScore )
      # intensity uses max pooling
      intensityMap.addScore_max( cStart, rStart, cEnd, rEnd, patchScore )
    self.massageRescoringMap( rescoringMap )
    localizationMap  = localizationMap * rescoringMap
    return localizationMap, intensityMap
  
  def massageRescoringMap( self, rescoringMap ):
    values = rescoringMap.cellValues
    uniqueValues = np.unique(values)
    uniqueValueThreshold = 3
    if len(uniqueValues) > uniqueValueThreshold:
      scoreMask = values < uniqueValues[-uniqueValueThreshold]
      values[scoreMask] = uniqueValues[-uniqueValueThreshold]
    values **= -1

  def inferIntermediateScales(self, targetScale, scale1, scale2):
    """Given pixelMap at two scales, infer localization of itermediate scale"""
    # localization
    avgLocalization = self.getLocalizationMap(scale1).copy()
    localization2 = self.getLocalizationMap(scale2)
    avgLocalization += localization2
    avgLocalization.cellValues /= 2
    # intensity
    avgIntensity = self.getIntensityMap(scale1).copy()
    intensity2 = self.getIntensityMap(scale2)
    avgIntensity += intensity2
    avgIntensity.cellValues /= 2
    self.pixelMaps += [{'scale': targetScale, \
      'localizationMap': avgLocalization, 'intensityMap': avgIntensity}]

  def getLocalizationMap(self, scale):
    """Return the localization map for this class and scale"""
    for pm in self.pixelMaps:
      if (pm['scale'] == scale):
        return pm['localizationMap']
    return None    

  def getIntensityMap(self, scale):
    """Return the intensity map for this class and scale"""
    for pm in self.pixelMaps:
      if (pm['scale'] == scale):
        return pm['intensityMap']
    return None    
