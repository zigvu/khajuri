import json
import numpy as np

from Logo.PipelineMath.PixelMap import PixelMap

from messaging.type.Headers import Headers
from hdf5Storage.infra.VideoDataReader import VideoDataReader


class HeatmapDataHandler(object):
  """Handle serving heatmap data"""

  def __init__(self, config):
    """Initialize values"""
    self.config = config
    self.logger = self.config.logging.logger
    self.allCellBoundariesDict = self.config.allCellBoundariesDict
    self.neighborMap = self.config.neighborMap

  def handle(self, headers, heatmapRequest):
    # request syntax should match in
    # kheer/services/messaging_services/heatmap_data.rb
    videoId = int(heatmapRequest['video_id'])
    chiaVersionId = int(heatmapRequest['chia_version_id'])
    frameNumber = int(heatmapRequest['frame_number'])
    scale = float(heatmapRequest['scale'])
    chiaClassId = str(heatmapRequest['chia_class_id'])

    responseHeaders = None
    responseMessage = None

    msg = "video_id: %d, chia_version_id: %d, frame_number: %d, scale: %f, chia_class_id: %s" % (
        videoId, chiaVersionId, frameNumber, scale, chiaClassId
    )

    try:
      # construct PixelMap
      pixelMap = PixelMap(self.allCellBoundariesDict, self.neighborMap, scale)
      with VideoDataReader(self.config, videoId, chiaVersionId) as vdr:
        frameData = vdr.getFrameData(frameNumber)
        patchScores = frameData.scores[:, chiaClassId]
        pixelMap.addScore_max(patchScores)
        # javascript expects int values between [0,100] inclusive
        cellValues = np.rint(pixelMap.cellValues * 100).tolist()

        data = {'scores': cellValues}

        msg = "Heatmap success: " + msg
        self.logger.info(msg)
        responseHeaders = Headers.statusSuccess()
        responseMessage = json.dumps(data)
    except Exception, e:
      # TODO: catch specific exceptions here
      msg = "Heatmap failure: " + msg
      self.logger.error(msg)
      responseHeaders = Headers.statusFailure(msg)
      responseMessage = json.dumps({'scores': []})

    return responseHeaders, responseMessage

  # both input/output are JSON
  def __call__(self, headers, message):
    return self.handle(headers, json.loads(message))
