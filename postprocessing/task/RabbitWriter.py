import numpy as np

from postprocessing.task.Task import Task

from hdf5Storage.type.FrameData import FrameData

from messaging.infra.Pickler import Pickler
from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient


class RabbitWriter(Task):

  def __init__(self, config, status):
    Task.__init__(self, config, status)
    self.logger.info('RabbitWriter: Starting writer')

    self.messagingCfg = self.config.messaging
    self.jobCfg = self.config.job

    amqp_url = self.messagingCfg.amqpURL
    serverQueueName = self.messagingCfg.queues.videoData
    self.rabbitWriter = RpcClient(amqp_url, serverQueueName, expectReply=False)

    self.videoId = self.jobCfg.videoId
    self.chiaVersionId = self.jobCfg.chiaVersionId

  def __call__(self, obj):
    frame, classIds = obj
    self.logger.debug('RabbitWriter: Frame Number: %d' % (frame.frameNumber))

    # extract data that needs to pass through network
    frameData = FrameData(self.videoId, self.chiaVersionId, frame.frameNumber)
    # get prob scores for zdist 0
    frameData.scores = frame.scores[0][:, :, 0].astype(np.float16)
    # get localizations for all zdist
    frameData.localizations = frame.localizations

    # send to storage queue
    message = Pickler.pickle(frameData)
    headers = Headers.videoStorageSave(self.videoId, self.chiaVersionId)
    self.rabbitWriter.call(headers, message)

    return (frame, classIds)
