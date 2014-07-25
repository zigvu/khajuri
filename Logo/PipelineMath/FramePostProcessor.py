from collections import OrderedDict
import numpy as np

from Logo.PipelineMath.ScaleSpaceCombiner import ScaleSpaceCombiner
from Logo.PipelineMath.PeaksExtractor import PeaksExtractor

class FramePostProcessor(object):
  def __init__(self, jsonReaderWriter, staticBoundingBoxes, configReader):
    """Initialize values"""
    self.jsonReaderWriter = jsonReaderWriter
    self.staticBoundingBoxes = staticBoundingBoxes
    self.configReader = configReader
    self.detectorThreshold = configReader.pp_detectorThreshold
    self.nonBackgroundClassIds = configReader.ci_nonBackgroundClassIds
    # cache computation
    self.classPixelMaps = {}

  def run(self):
    """Collect and analyze detection results"""
    # prevent double writing to json by deleting any previous writes
    self.jsonReaderWriter.initializeLocalizations()
    self.jsonReaderWriter.initializeCurations()
    # TODO TODO TODO TODO TODO TODO TODO TODO TODO 
    # TODO: update jsonReaderWriter with re-normalized scores
    # combine detection scores in scale space
    scaleSpaceCombiner = ScaleSpaceCombiner(self.staticBoundingBoxes, self.jsonReaderWriter)
    # for each class except background classes, get localization and curation bboxes
    for classId in self.nonBackgroundClassIds:
      # ---------------- BEGIN: localization ---------------- 
      # get best pixelMap - result of averaging and maxPooling
      localizationPixelMap = scaleSpaceCombiner.getBestInferredPixelMap(classId)
      # extract all detected bboxes above threshold 
      localizationPeaks = PeaksExtractor(localizationPixelMap, \
        self.configReader, self.staticBoundingBoxes.imageDim)
      localizationPatches = localizationPeaks.getPeakBboxes(self.detectorThreshold)
      # save inferred localization patches to json
      for lp in localizationPatches:
        self.jsonReaderWriter.addLocalization(classId, lp['bbox'].json_format(), lp['intensity'])
      # ---------------- END: localization ---------------- 
      # ---------------- BEGIN: curation ---------------- 
      # get best pixelMap - result of maxPooling only
      curationPixelMap = scaleSpaceCombiner.getBestIntensityPixelMap(classId)
      # extract all curation bboxes and associated intensity
      curationPeaks = PeaksExtractor(curationPixelMap, \
        self.configReader, self.staticBoundingBoxes.imageDim)
      curationPatches = curationPeaks.getPatchesForCuration()
      # save curation patches to json
      for cp in curationPatches:
        self.jsonReaderWriter.addCuration(classId, cp['bbox'].json_format(), cp['intensity'])
      # ---------------- END: curation ---------------- 
      # caching
      self.classPixelMaps[classId] = {'localizationMap': localizationPixelMap, \
        'intensityMap': curationPixelMap}
    # save json
    self.jsonReaderWriter.saveState()

  def saveLocalizations(self, filename):
    """Save localization calculations to filename in npz format"""
    localizationMaps = OrderedDict()
    for classId in self.nonBackgroundClassIds:
      localizationMaps[classId] = self.classPixelMaps[classId]['localizationMap']
    np.savez_compressed(filename, **(localizationMaps))
