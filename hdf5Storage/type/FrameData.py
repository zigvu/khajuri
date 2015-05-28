class FrameData( object ):
  def __init__( self, videoId, chiaVersionId, frameNumber ):
    self.videoId = videoId
    self.chiaVersionId = chiaVersionId
    self.frameNumber = frameNumber
    self.scores = None
    self.localizations = None

  # Note: this format corresponds to mongo schema in
  # kheer/app/models/khajuri_data/localization.rb
  def getLocalizationArr( self ):
    lArr = []
    if self.localizations != None:
      for clsId, locs in self.localizations.iteritems():
        for loc in locs:
          lArr += [{\
            'video_id': self.videoId,
            'chia_version_id': self.chiaVersionId,
            'frame_number': self.frameNumber,
            'chia_class_id': clsId,
            'score': loc.score,
            'zdist_thresh': loc.zDistThreshold,
            'scale': loc.scale,
            'x': loc.rect.x, 'y': loc.rect.y, 'w': loc.rect.w, 'h': loc.rect.h
          }]
    return lArr

  def __str__( self ):
    return 'FrameData(%d, %d, %d)' % ( \
      self.videoId, self.chiaVersionId, self.frameNumber )
