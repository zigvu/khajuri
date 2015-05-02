import logging
from Logo.PipelineMath.ScaleSpaceCombiner import ScaleSpaceCombiner
from Logo.PipelineMath.PeaksExtractor import PeaksExtractor
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

class FramePostProcessor(object):
  def __init__(self, classId, config, frame, zDistThreshold ):
    """Initialize values"""
    self.classId = classId
    self.config = config
    self.frame = frame
    self.zDistThreshold = zDistThreshold
    #self.frame.initializeLocalizations()
    #self.frame.initializeCurations()

  def localize(self):
    """Collect and analyze detection results"""
    scaleSpaceCombiner = ScaleSpaceCombiner(self.classId, self.config, self.frame, self.zDistThreshold )
    localizationPixelMap = scaleSpaceCombiner.getBestInferredPixelMap()
    localizationPixelMap.setScale( 1.0 )
    localizationPeaks = PeaksExtractor(localizationPixelMap, self.config )
    localizationPatches = localizationPeaks.getPeakBboxes()
    for lp in localizationPatches:
      logging.info( 'Localization at: %s, with intensity: %s for class %s and zDist %s'
          % ( lp['bbox'].json_format(), lp['intensity'], self.classId, self.zDistThreshold ) )
      rect = Rect( lp['bbox'].x0, lp['bbox'].y0, lp['bbox'].width, lp['bbox'].height )
      l = Localization( self.zDistThreshold, self.classId, rect, lp[ 'intensity' ], 1 )
      self.frame.addLocalization( self.classId, l )
    return localizationPatches
