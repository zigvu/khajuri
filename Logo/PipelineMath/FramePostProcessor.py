from collections import OrderedDict
import numpy as np
import logging

from Logo.PipelineMath.ScaleSpaceCombiner import ScaleSpaceCombiner
from Logo.PipelineMath.PeaksExtractor import PeaksExtractor

class FramePostProcessor(object):
  def __init__(self, jsonReaderWriter, staticBoundingBoxes, configReader, allCellBoundariesDict):
    """Initialize values"""
    self.jsonReaderWriter = jsonReaderWriter
    self.staticBoundingBoxes = staticBoundingBoxes
    self.configReader = configReader
    self.detectorThreshold = configReader.pp_detectorThreshold
    self.nonBackgroundClassIds = configReader.ci_nonBackgroundClassIds
    self.allCellBoundariesDict = allCellBoundariesDict
    self.compressedJSON = configReader.pp_compressedJSON
    self.savePatchScores = configReader.pp_savePatchScores

    # cache computation
    self.classPixelMaps = {}

  def run(self):
    """Collect and analyze detection results"""
    # prevent double writing to json by deleting any previous writes
    self.jsonReaderWriter.initializeLocalizations()
    self.jsonReaderWriter.initializeCurations()
    # TODO TODO TODO TODO TODO TODO TODO TODO TODO 
    # TODO: update jsonReaderWriter with re-normalized scores
    # for each class except background classes, get localization and curation bboxes
    classesAboveThreshold, classesbelowThreshold =\
        self.jsonReaderWriter.getClassesSplit( self.detectorThreshold )
    logging.info( 'Frame %s, classesAboveThreshold %s, classesbelowThreshold %s' % 
        ( self.jsonReaderWriter.getFrameNumber(), classesAboveThreshold, classesbelowThreshold ) )
    for classId in classesAboveThreshold:
      if classId not in self.nonBackgroundClassIds:
        logging.info( 'Skipping classId %s as its a back ground class' % classId )
        continue
      # combine detection scores in scale space
      scaleSpaceCombiner = ScaleSpaceCombiner(classId, self.staticBoundingBoxes,\
          self.jsonReaderWriter, self.allCellBoundariesDict )
      # ---------------- BEGIN: localization ---------------- 
      # get best pixelMap - result of averaging and maxPooling
      localizationPixelMap = scaleSpaceCombiner.getBestInferredPixelMap()
      localizationPixelMap.setScale( 1.0 )
      # extract all detected bboxes above threshold 
      localizationPeaks = PeaksExtractor(localizationPixelMap.toNumpyArray(), \
        self.configReader, self.staticBoundingBoxes.imageDim)
      localizationPatches = localizationPeaks.getPeakBboxes(self.detectorThreshold)
      # save inferred localization patches to json
      for lp in localizationPatches:
        self.jsonReaderWriter.addLocalization(classId, lp['bbox'].json_format(), lp['intensity'])
      # ---------------- END: localization ---------------- 
      # ---------------- BEGIN: curation ---------------- 
      # get best pixelMap - result of maxPooling only
      if self.configReader.ci_computeFrameCuration:
        curationPixelMap = scaleSpaceCombiner.getBestIntensityPixelMap()
        curationPixelMap.setScale( 1.0 )
        # extract all curation bboxes and associated intensity
        curationPeaks = PeaksExtractor(curationPixelMap.toNumpyArray(), \
          self.configReader, self.staticBoundingBoxes.imageDim)
        curationPatches = curationPeaks.getPatchesForCuration()
        # save curation patches to json
        for cp in curationPatches:
          self.jsonReaderWriter.addCuration(classId, cp['bbox'].json_format(), cp['intensity'])
      # ---------------- END: curation ---------------- 
      # caching
      self.classPixelMaps[classId] = {'localizationMap': localizationPixelMap}
    # save json
    self.jsonReaderWriter.saveState(compressed_json = self.compressedJSON, \
      save_patch_scores = self.savePatchScores)
    return True

  def saveLocalizations(self, numpyFileBaseName):
    """Save localization calculations to different files in npy format"""
    for classId in self.nonBackgroundClassIds:
      clsFilename = "%s_%s.npy" % (numpyFileBaseName, str(classId))
      np.save(clsFilename, self.classPixelMaps[classId]['localizationMap'])
