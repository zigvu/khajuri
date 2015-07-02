from messaging.infra.Pickler import Pickler
from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient

from config.ZLogging import ZLoggingStreamHandler

class LogConsolidator(object):
  """Consolidate logs from all threads"""

  def __init__(self, config):
    """Initialization"""
    self.config = config
    self.loggingCfg = self.config.logging
    self.storageCfg = self.config.storage
    self.messagingCfg = self.config.messaging

    self.logQueue = self.loggingCfg.logQueue
    # print to stdio
    self.zLoggingStreamHandler = ZLoggingStreamHandler()
    # if enabled, also write to rabbit
    if self.loggingCfg.rabbitLoggerEnabled:
      # create rabbit log writer
      amqp_url = self.messagingCfg.amqpURL
      serverQueueName = self.messagingCfg.queues.log
      self.rabbitLogWriter = RpcClient(amqp_url, serverQueueName, expectReply=False)

  def startConsolidation(self):
    """Write logs to all output"""
    while True:
      logRecord = self.logQueue.get()
      # all logs are generated
      if logRecord is None:
        self.logQueue.task_done()
        # poison pill means done with logging
        break
      # print to stdio
      self.zLoggingStreamHandler.handle(logRecord)
      # if enabled, also write to rabbit
      if self.loggingCfg.rabbitLoggerEnabled:
        # send to storage queue
        message = Pickler.pickle(logRecord)
        headers = Headers.log()
        self.rabbitLogWriter.call(headers, message)
      self.logQueue.task_done()
    # done with all logs
    if self.loggingCfg.rabbitLoggerEnabled:
      self.rabbitLogWriter.close()
