import logging

from Logo.PipelineMath.ScaleSpaceCombiner import ScaleSpaceCombiner
from Logo.PipelineMath.PeaksExtractor import PeaksExtractor

from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect
from Queue import PriorityQueue


class FramePostProcessor(object):
  """Create localizations for a particular class"""

  def __init__(self, classId, config, frame, zDistThreshold):
    """Initialize values"""
    self.classId = classId
    self.config = config
    self.frame = frame
    self.zDistThreshold = zDistThreshold

  def localize(self):
    """Collect and analyze detection results"""
    localizations = PriorityQueue()
    scaleSpaceCombiner = ScaleSpaceCombiner(
        self.classId, self.config, self.frame, self.zDistThreshold)
    for lclzOrigScale in sorted( self.config.sw_scales, reverse=True ):
      lclzPixelMap = scaleSpaceCombiner.pixelMapper.getScaleDecayedMap(lclzOrigScale)
      lclzPixelMap.setScale(1.0)
      lclzPeaks = PeaksExtractor(lclzPixelMap, self.config)
      lclzPatches = lclzPeaks.getPeakBboxes()
      for lp in lclzPatches:
        logging.info(
            'Localization at: %s, with intensity: %s for class %s and zDist %s and orig scale %s.' %
            (lp['bbox'].json_format(), lp['intensity'], self.classId,
             self.zDistThreshold, lclzOrigScale ) )
        rect = Rect(
            lp['bbox'].x0, lp['bbox'].y0, lp['bbox'].width, lp['bbox'].height)
        l = Localization(
            self.zDistThreshold, self.classId, rect, lp['intensity'],
            lclzOrigScale)
        localizations.put( ( l.rect.area, l ) )
    chosenLocalizations = []
    while not localizations.empty():
      intersects = False
      score, l = localizations.get()
      for existingLocalization in chosenLocalizations:
        if l.rect.intersect( existingLocalization ) >= 0.2 * l.rect.area \
            or l.rect.intersect( existingLocalization ) >= existingLocalization.area \
            or l.rect.centerDistance( existingLocalization ) < 50:
          intersects = True
      if not intersects and l.score > 0.3:
        logging.info( 'Chosen localization %s' % l )
        self.frame.addLocalization(self.classId, l)
        chosenLocalizations.append( l.rect )
      else:
        logging.info( 'Discard localization %s' % l )

    return None
