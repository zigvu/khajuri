
class LogConsolidator(object):
  """Consolidate logs from all threads"""

  def __init__(self, config):
    """Initialization"""
    self.config = config


  def setupQueues(self, logQueue):
    """Setup queues"""
    self.logQueue = logQueue

  def startConsolidation(self):
    """Write logs to all output"""
    while True:
      logMsg = self.logQueue.get()
      # all logs are generated
      if logMsg is None:
        self.logQueue.task_done()
        # poison pill means done with logging
        break
      # generated logs
      print "%s" % logMsg
      self.logQueue.task_done()
