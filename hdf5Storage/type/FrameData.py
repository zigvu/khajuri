class FrameData(object):
  """Data structure to hold post-processing results and raw data to
  transport across network
  """

  def __init__(self, videoId, chiaVersionId, frameNumber):
    """Initialize values"""
    self.videoId = videoId
    self.chiaVersionId = chiaVersionId
    self.frameNumber = frameNumber
    self.scores = None
    self.localizations = None

  # Note:
  # Need to cast to JSON serializable values in case of numpy
  # data type pollution in incoming Frame data structure
  # Note: this format corresponds to formatter in
  # kheer/app/data_importers/formatters/localization_formatter.rb
  def getLocalizationArr(self):
    lArr = []
    if self.localizations != None:
      for clsId, locs in self.localizations.iteritems():
        for loc in locs:
          lArr += [{
              'video_id': int(self.videoId),
              'chia_version_id': int(self.chiaVersionId),
              'frame_number': int(self.frameNumber),
              'chia_class_id': int(clsId),
              'score': float(loc.score),
              'zdist_thresh': float(loc.zDistThreshold),
              'scale': float(loc.scale),
              'x': int(loc.rect.x),
              'y': int(loc.rect.y),
              'w': int(loc.rect.w),
              'h': int(loc.rect.h)
          }]
    return lArr

  def __str__(self):
    return 'FrameData(%d, %d, %d)' % (
        self.videoId, self.chiaVersionId, self.frameNumber
    )
