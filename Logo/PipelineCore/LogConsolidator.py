from messaging.infra.Pickler import Pickler
from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient

from config.ZLogging import ZLoggingStreamHandler

class LogConsolidator(object):
  """Consolidate logs from all threads"""

  def __init__(self, config):
    """Initialization"""
    self.config = config
    self.logQueue = self.config.logQueue
    if self.config.lg_rabbit_logger:
      # create rabbit log writer
      amqp_url = self.config.mes_amqp_url
      serverQueueName = self.config.mes_q_vm2_khajuri_development_log
      self.rabbitLogWriter = RpcClient(amqp_url, serverQueueName, expectReply=False)
    else:
      self.zLoggingStreamHandler = ZLoggingStreamHandler()


  def startConsolidation(self):
    """Write logs to all output"""
    while True:
      logRecord = self.logQueue.get()
      # all logs are generated
      if logRecord is None:
        self.logQueue.task_done()
        # poison pill means done with logging
        break
      if self.config.lg_rabbit_logger:
        # send to storage queue
        message = Pickler.pickle(logRecord)
        headers = Headers.log(self.config.kheerJobId)
        self.rabbitLogWriter.call(headers, message)
      else:
        self.zLoggingStreamHandler.handle(logRecord)
      self.logQueue.task_done()
    if self.config.lg_rabbit_logger:
      self.rabbitLogWriter.close()
