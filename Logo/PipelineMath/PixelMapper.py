import math
import numpy as np
import scipy.ndimage as ndimage
from PixelMap import PixelMap

class PixelMapper(object):
  def __init__(self, classId, staticBoundingBoxes, configReader, jsonReaderWriter, allCellBoundariesDict ):
    """Initialize pixelMap according to dimensions of image and sliding window"""
    self.classId = classId
    self.staticBoundingBoxes = staticBoundingBoxes
    self.configReader = configReader
    self.detectorThreshold = self.configReader.pp_detectorThreshold
    self.sigmoidCenter = self.configReader.sw_scale_decay_sigmoid_center
    self.sigmoidSteepness = self.configReader.sw_scale_decay_sigmoid_steepness

    self.origImageShape = (staticBoundingBoxes.imageDim.height, staticBoundingBoxes.imageDim.width)
    self.jsonReaderWriter = jsonReaderWriter
    self.pixelMaps = []
    self.scales = jsonReaderWriter.getScalingFactors()
    self.allCellBoundariesDict = allCellBoundariesDict
    for scale in self.scales:
      localizationMap, intensityMap = self.populatePixelMap(scale)
      self.pixelMaps += [{'scale': scale, \
        'localizationMap': localizationMap, \
        'intensityMap': intensityMap,\
        'decayedMap': None}]

  def populatePixelMap(self, scale):
    """Initialize the pixel map for the class at given scale"""
    mapAllCellCount = PixelMap( self.allCellBoundariesDict, scale )
    mapDetectionCellCount = PixelMap( self.allCellBoundariesDict, scale )
    intensityMap = PixelMap( self.allCellBoundariesDict, scale )
    for patch in self.jsonReaderWriter.getPatches(scale):
      rStart = patch['patch']['y']
      rEnd = patch['patch']['y'] + patch['patch']['height']
      cStart = patch['patch']['x']
      cEnd = patch['patch']['x'] + patch['patch']['width']
      patchScore = float(patch['scores'][self.classId])
      # add scores to rescoring patches
      mapAllCellCount.addScore( cStart, rStart, cEnd, rEnd, 1 ) 
      if patchScore > self.detectorThreshold:
        mapDetectionCellCount.addScore( cStart, rStart, cEnd, rEnd, 1) 
      # intensity uses max pooling
      intensityMap.addScore_max( cStart, rStart, cEnd, rEnd, patchScore )
    # create localization from intensity
    self.massageRescoringMap(mapAllCellCount, mapDetectionCellCount)
    localizationMap = mapAllCellCount * intensityMap
    return localizationMap, intensityMap

 
  def spikeDetection( self, mapAllCellCount ):
    self.spikeDetectionUsingCellMap( mapAllCellCount )

  def spikeDetectionUsingCellMap( self, mapAllCellCount ):
    # Zero Out all Pixels below threshold
    threshold = 1
    maxima = mapAllCellCount.copy()
    diff = ( maxima.cellValues > threshold )
    maxima.cellValues[ diff == 0 ] = 0

    # 1. Find cell Indexes with a positive value
    posValueSet = set()
    for i in np.argwhere( diff ):
      posValueSet.add( i[0] )

    # 2. Find Islands and update their value
    while len( posValueSet ) > 0:
      i = posValueSet.pop()
      neighbors, maxValue, avgValue, cb = maxima.BFS( i )
      posValueSet.difference_update( neighbors.difference( set( [i] ) ) )
      maxima.cellValues[ list( neighbors) ] =\
          maxima.cellValues[ list( neighbors ) ] / ( 1.0 * maxValue )
      maxima.cellValues[ list( neighbors ) ] = 1.0/( 1.0 
            + np.exp( -2 * ( maxima.cellValues[ list( neighbors ) ] - self.sigmoidCenter ) *
              self.sigmoidSteepness ) )

    # 3. Find bounding Boxes ?
    mapAllCellCount.cellValues = maxima.cellValues

  def spikeDetectionUsingNumpy( self, mapAllCellCount ):
    npPixelMap = mapAllCellCount.toNumpyArray()
    rescoringMap = np.zeros(np.shape(npPixelMap))
    binaryStructure = ndimage.morphology.generate_binary_structure(2,2)
    threshold = 1
    # zero out all pixels below threshold
    maxima = npPixelMap.copy()
    diff = (maxima > threshold)
    maxima[diff == 0] = 0
    # label each non-contiguous area with integer values
    labeledArray, num_objects = ndimage.label(maxima, structure= binaryStructure)
    # find center of each labeled non-contiguous area
    xy = np.array(ndimage.center_of_mass(maxima, labeledArray, range(1, num_objects + 1)))
    # find bounding boxes
    for idx, coord in enumerate(xy):
      # zero out all pixels that don't belong to this label
      labelArea = labeledArray == (idx + 1)
      # find end points of the array containing label
      labelWhere = np.argwhere(labelArea)
      (yStart, xStart), (yEnd, xEnd) = labelWhere.min(0), labelWhere.max(0) + 1
      # set values for the labels
      maxDetectionCount = np.max(npPixelMap[yStart:yEnd, xStart:xEnd][labelArea[yStart:yEnd, xStart:xEnd]])
      npPixelMap[yStart:yEnd, xStart:xEnd][labelArea[yStart:yEnd, xStart:xEnd]] = \
        npPixelMap[yStart:yEnd, xStart:xEnd][labelArea[yStart:yEnd, xStart:xEnd]] / maxDetectionCount
      rescoringMap[yStart:yEnd, xStart:xEnd][labelArea[yStart:yEnd, xStart:xEnd]] = \
        1.0/(1.0 + np.exp(-2 * (npPixelMap[yStart:yEnd, xStart:xEnd][labelArea[yStart:yEnd, xStart:xEnd]]\
           - self.sigmoidCenter) * self.sigmoidSteepness))
    mapAllCellCount.fromNumpyArray(rescoringMap)

  def massageRescoringMap(self, mapAllCellCount, mapDetectionCellCount):
    """Rescore localization to highlight positive detections"""
    # if there is not a single detection, skip arithmetic
    maxDetectionCount = np.max(mapDetectionCellCount.cellValues)
    if maxDetectionCount <= 0:
      mapAllCellCount.cellValues = 0
      return
    # TODO: config tuning of sigmoid values for each scale

    # STEP 1: 
    # adjust for patches in edges and corners
    # spike detection counts when number of cell visit is low but a detection happened
    mapAllCellCount.cellValues = mapDetectionCellCount.cellValues/mapAllCellCount.cellValues
    mapAllCellCount.cellValues = 1.0/(1.0 + np.exp(-2 * \
      (mapAllCellCount.cellValues - self.sigmoidCenter) * self.sigmoidSteepness))
    # STEP 2:
    # even if score count of edge patches is not originally high,
    # make them contribute significantly towards final bbox
    mapAllCellCount.cellValues *= (maxDetectionCount/2.0)
    mapAllCellCount.cellValues += mapDetectionCellCount.cellValues

    # STEP 3:
    # spike detections
    self.spikeDetection( mapAllCellCount )

    # maxDetectionCount = np.max(mapAllCellCount.cellValues)
    # mapAllCellCount.cellValues /= maxDetectionCount
    # mapAllCellCount.cellValues = 1.0/(1.0 + np.exp(-2 * (mapAllCellCount.cellValues - self.sigmoidCenter) * self.sigmoidSteepness))

  def getScaleDecayedMap(self, scale):
    """Given decay factors, combines different scores across scales"""
    # if in cache, return
    for pm in self.pixelMaps:
      if pm['scale'] == scale and pm['decayedMap'] != None:
        return pm['decayedMap']
    # else, create map by combining decay factors
    decayedMap = PixelMap(self.allCellBoundariesDict, scale)
    decayFactors = None
    for df in self.allDecayFactors:
      if df['scale'] == scale:
        decayFactors = df['factors']
    for decayFactor in decayFactors:
      dScale = decayFactor['scale']
      dFactor = decayFactor['factor']
      # check to see if in cache
      decayMultipliedPm = None
      for dmpm in self.decayMultipliedPixelMaps:
        if dmpm['scale'] == dScale and dmpm['factor'] == dFactor:
          decayMultipliedPm = dmpm['pixelMap']
          break
      # if not in cache, create
      if decayMultipliedPm == None:
        decayMultipliedPm = self.getLocalizationMap(dScale).copy()
        decayMultipliedPm.cellValues *= dFactor
        # and store in cache
        for dmpm in self.decayMultipliedPixelMaps:
          if dmpm['scale'] == dScale and dmpm['factor'] == dFactor:
            dmpm['pixelMap'] = decayMultipliedPm
            break
      # add this decay multiplied pixelMap to final map
      decayedMap = decayedMap + decayMultipliedPm
    # save in cache
    for pm in self.pixelMaps:
      if pm['scale'] == scale:
        pm['decayedMap'] = decayedMap
        break
    # return
    return decayedMap

  def setupScaleDecayedMapCache(self, allDecayFactors):
    """Set up data structure to hold all intermediate calculation
    during scale decayed maps"""
    self.allDecayFactors = allDecayFactors
    self.decayMultipliedPixelMaps = []
    for decayFactors in allDecayFactors:
      for decayFactor in decayFactors['factors']:
        dScale = decayFactor['scale']
        dFactor = decayFactor['factor']
        dfAbsent = True
        for dmpm in self.decayMultipliedPixelMaps:
          if dmpm['scale'] == dScale and dmpm['factor'] == dFactor:
            dfAbsent = False
            break
        if dfAbsent:
          self.decayMultipliedPixelMaps.append({'scale': dScale, 'factor': dFactor, 'pixelMap': None})
    # done

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
