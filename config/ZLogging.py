import socket
import logging

class  ZFormatter(logging.Formatter):
  """Specialized log formatter to help in logging analytics"""
  # Format as per issue 104
  # LOG Format:
  # [machine_hostname]::[kheer_job_id]::[log_level]::[date_time]::[file_name]::
  # [line_number]::[process_id]::[message]
  # TIME Format:
  # [Year]-[Month]-[DAY]:[HOUR]-[MINUTE]-[SECOND]

  def __init__(self, formatMsg):
    """Init"""
    logging.Formatter.__init__(self)
    self.hostName = socket.gethostname()
    self.datefmt = '%Y-%m-%d:%H-%M-%S'
    self.kheerJobId = 0
    if 'kheer_job_id' in formatMsg:
      self.kheerJobId = formatMsg['kheer_job_id']

  def format(self, record):
    """Correctly formatted log"""
    msg = '%s' % (self.hostName)
    msg = '%s::%s' % (msg, self.kheerJobId)
    msg = '%s::%s' % (msg, record.levelname)
    msg = '%s::%s' % (msg, self.formatTime(record, self.datefmt))
    msg = '%s::%s' % (msg, record.filename)
    msg = '%s::%s' % (msg, record.lineno)
    msg = '%s::%s' % (msg, record.process)
    msg = '%s::%s' % (msg, record.getMessage())
    return msg



class ZLoggingStreamHandler(logging.StreamHandler):
  """Handler to write to std io"""
  def __init__(self, formatMsg):
    logging.StreamHandler.__init__(self)
    # since this is directly going to stdio, we don't
    # need to explicitely format the message - formatter
    # will take care of that
    self.setFormatter(ZFormatter(formatMsg))



class ZLoggingQueueHandler(logging.Handler):
  """Handler to write to log queue"""
  def __init__(self, logQueue, formatMsg):
    logging.Handler.__init__(self)
    self.logQueue = logQueue
    # rather than sending LogRecord object to our queue,
    # we send the formatted strings
    # self.setFormatter(ZFormatter(formatMsg))
    self.zformatter = ZFormatter(formatMsg)

  def emit(self, record):
    """Write to queue"""
    self.logQueue.put(self.zformatter.format(record))



class ZLoggingQueueProducer(object):
  """Produce logs from non-main process/threads"""
  def __init__(self, logQueue, logLevel, formatMsg):
    self.logger = logging.getLogger('zigvu.khajuri')
    self.logger.setLevel(logLevel)

    for handler in self.logger.handlers:
      assert not isinstance(handler, ZLoggingQueueHandler)
      self.logger.removeHandler(handler)
    # add the queue handler
    handler = ZLoggingQueueHandler(logQueue, formatMsg)
    self.logger.addHandler(handler)
    self.logger.propagate = False

  def getLogger(self):
    return self.logger



class ZLogging(object):
  def __init__(self, logLevel, formatMsg):
    self.logger = logging.getLogger('zigvu.khajuri')
    self.logger.setLevel(logLevel)
    self.logger.addHandler(ZLoggingStreamHandler(formatMsg))

  def getLogger(self):
    return self.logger
