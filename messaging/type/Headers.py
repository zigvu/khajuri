# NOTE: this file corresponds to kheer/app/messaging/headers.rb
class Headers(object):
  """Headers for RabbitMq communication/handshakes"""

  def __init__():
    pass

  # Types: status, data
  # status states:
  #   success
  #   failure
  # data states: 
  #   video
  #     storage
  #       start
  #       end
  #     clip_id

  # status headers
  # -----------------------------------------------
  @staticmethod
  def statusSuccess():
    headers = {'type': 'status', 'state': 'success', 'props': {}}
    return headers

  @staticmethod
  def statusFailure(failureCause):
    headers = {
        'type': 'status',
        'state': 'failure',
        'props': {'cause': failureCause}
    }
    return headers

  @staticmethod
  def isStatusSuccess(headers):
    return headers['type'] == 'status' and headers['state'] == 'success'

  @staticmethod
  def isStatusFailure(headers):
    return headers['type'] == 'status' and headers['state'] == 'failure'

  @staticmethod
  def getStatusFailureCause(headers):
    failureCause = None
    if Headers.isStatusFailure(headers):
      failureCause = headers['props']['cause']
    return failureCause

  # data headers
  # -----------------------------------------------
  @staticmethod
  def videoStorageStart(videoId, chiaVersionId):
    headers = {
        'type': 'data',
        'state': 'video.storage.start',
        'props': {'video_id': videoId, 'chia_version_id': chiaVersionId}
    }
    return headers

  @staticmethod
  def videoStorageEnd(videoId, chiaVersionId):
    headers = {
        'type': 'data',
        'state': 'video.storage.end',
        'props': {'video_id': videoId, 'chia_version_id': chiaVersionId}
    }
    return headers

  @staticmethod
  def videoStorageSave(videoId, chiaVersionId):
    headers = {
        'type': 'data',
        'state': 'video.storage.save',
        'props': {'video_id': videoId, 'chia_version_id': chiaVersionId}
    }
    return headers

  @staticmethod
  def clipId(videoId):
    headers = {
        'type': 'data',
        'state': 'video.clip_id',
        'props': {'video_id': videoId}
    }
    return headers

  @staticmethod
  def isVideoStorageStart(headers):
    return ((headers['type'] == 'data') and
            (headers['state'] == 'video.storage.start'))

  @staticmethod
  def isVideoStorageEnd(headers):
    return headers['type'] == 'data' and headers['state'] == 'video.storage.end'

  @staticmethod
  def isVideoStorageSave(headers):
    return ((headers['type'] == 'data') and
            (headers['state'] == 'video.storage.save'))

  @staticmethod
  def getPropsVideoId(headers):
    return int(headers['props']['video_id'])

  @staticmethod
  def getPropsChiaVersionId(headers):
    return int(headers['props']['chia_version_id'])
