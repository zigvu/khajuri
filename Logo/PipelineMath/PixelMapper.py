import math
import numpy as np
import scipy.ndimage as ndimage
from PixelMap import PixelMap
import matplotlib.pyplot as plt

class PixelMapper(object):
  mapAllCellCountCache = {}

  def __init__(self, classId, config, frame, zDistThreshold ):
    """Initialize pixelMap according to dimensions of image and sliding window"""
    self.classId = classId
    self.config = config
    self.frame = frame
    self.sigmoidCenter = self.config.sw_scale_decay_sigmoid_center
    self.sigmoidSteepness = self.config.sw_scale_decay_sigmoid_steepness
    self.zDistThreshold = zDistThreshold
    self.pixelMaps = []
    patchScores = frame.scores[ self.zDistThreshold ][ :, self.classId, 0 ]
    oneScores = np.ones( len( patchScores ), dtype=np.float )
    self.mapAllCellCount = {}
    for scale in self.config.sw_scales:
      if not PixelMapper.mapAllCellCountCache.get( scale ):
        PixelMapper.mapAllCellCountCache[ scale ] = PixelMap( self.config.allCellBoundariesDict, scale )
        PixelMapper.mapAllCellCountCache[ scale ].addScore( oneScores )
      localizationMap, intensityMap = self.populatePixelMap(scale)
      self.pixelMaps += [{'scale': scale, \
        'localizationMap': localizationMap, \
        'intensityMap': intensityMap,\
        'decayedMap': None}]

  #@profile
  def populatePixelMap(self, scale):
    """Initialize the pixel map for the class at given scale"""
    mapAllCellCount = PixelMapper.mapAllCellCountCache[ scale ].copy()
    mapDetectionCellCount = PixelMap( self.config.allCellBoundariesDict, scale )
    intensityMap = PixelMap( self.config.allCellBoundariesDict, scale )
    
    # Map Patch Scores to cellValues 
    patchScores = self.frame.scores[ self.zDistThreshold ][ :, self.classId, 0 ]
    patchScoresAboveThreshold = np.zeros( len( patchScores ), dtype=np.float )
    patchScoresAboveThreshold[ patchScores > self.config.pp_detectorThreshold ] = 1
    mapDetectionCellCount.addScore( patchScoresAboveThreshold )
    intensityMap.addScore_max( patchScores )

    # Massage the cellValues
    self.massageRescoringMap(mapAllCellCount, mapDetectionCellCount)
    localizationMap = mapAllCellCount * intensityMap
    return localizationMap, intensityMap

  #@profile
  def spikeDetection( self, mapAllCellCount ):
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
    mapAllCellCount.cellValues = maxima.cellValues

  def massageRescoringMap(self, mapAllCellCount, mapDetectionCellCount):
    """Rescore localization to highlight positive detections"""
    # if there is not a single detection, skip arithmetic
    maxDetectionCount = np.max(mapDetectionCellCount.cellValues)
    if maxDetectionCount <= 0:
      mapAllCellCount.cellValues = 0
      return

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

  #@profile
  def getScaleDecayedMap(self, scale):
    """Given decay factors, combines different scores across scales"""
    # if in cache, return
    for pm in self.pixelMaps:
      if pm['scale'] == scale and pm['decayedMap'] != None:
        return pm['decayedMap']
    # else, create map by combining decay factors
    decayedMap = PixelMap(self.config.allCellBoundariesDict, scale)
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

  #@profile
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
