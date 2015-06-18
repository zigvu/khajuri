import logging
import numpy as np

from postprocessing.task.Task import Task

from hdf5Storage.type.FrameData import FrameData

from messaging.infra.Pickler import Pickler
from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient


class RabbitWriter(Task):

  def __init__(self, config, status):
    Task.__init__(self, config, status)
    logging.debug('RabbitWriter: Starting writer')
    amqp_url = self.config.mes_amqp_url
    serverQueueName = self.config.mes_q_vm2_kahjuri_development_video_data
    self.rabbitWriter = RpcClient(amqp_url, serverQueueName, expectReply=False)

  def __call__(self, obj):
    frame, classIds = obj
    logging.info(
        'RabbitWriter: Saving frameInfo on %s for classes %s' %
        (frame, classIds))

    # extract data that needs to pass through network
    frameData = FrameData(
        self.config.videoId, self.config.chiaVersionId, frame.frameNumber)
    # get prob scores for zdist 0
    frameData.scores = frame.scores[0][:, :, 0].astype(np.float16)
    # get localizations for all zdist
    frameData.localizations = frame.localizations

    # send to storage queue
    message = Pickler.pickle(frameData)
    headers = Headers.videoStorageSave(
        self.config.videoId, self.config.chiaVersionId)
    self.rabbitWriter.call(headers, message)

    return (frame, classIds)
