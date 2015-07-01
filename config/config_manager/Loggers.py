import logging
from multiprocessing import JoinableQueue
from config.ZLogging import ZLogging, ZLoggingQueueProducer

class Loggers(object):
  """Sets up logger related configs"""

  def __init__(self, configHash, logExtraParams):
    """Initialize variables"""
    lgHash = configHash['execution']['logging']
    lgLvl = lgHash['log_level']

    self.logLevel = logging.DEBUG
    if lgLvl == 'INFO':
      self.logLevel = logging.INFO
    if lgLvl == 'ERROR':
      self.logLevel = logging.ERROR
    if lgLvl == 'CRITICAL':
      self.logLevel = logging.CRITICAL

    self.rabbitLoggerEnabled = lgHash['rabbit_writer'] == True
    self.needsLogQueue = lgHash['needs_log_queue'] == True

    if self.rabbitLoggerEnabled:
      self.logLevel = logging.INFO
      self.needsLogQueue = True

    if self.needsLogQueue:
      self.logQueue = JoinableQueue()
      self.logger = ZLoggingQueueProducer(
          self.logQueue, self.logLevel, logExtraParams).getLogger()
    else:
      self.logger = ZLogging(self.logLevel, logExtraParams).getLogger()

    self.cppGlogStarted = False
