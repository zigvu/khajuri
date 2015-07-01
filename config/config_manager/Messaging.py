
class Messaging(object):
  """Sets up messaging related configs"""
  def __init__(self, configHash, environment):
    """Initialize variables"""
    self.amqpURL = configHash['rabbit']['amqp_url']
    queueHash = configHash['rabbit']['queue_names'][environment]
    self.queues = RabbitQueues(queueHash)


class RabbitQueues(object):
  """Queue names"""
  def __init__(self, qHash):
    """Initialize variables"""
    self.log = qHash['log']
    self.videoData = qHash['video_data']
    self.clipIdRequest = qHash['clip_id_request']
    self.heatmapRequest = qHash['heatmap_request']
    self.localizationRequest = qHash['localization_request']
