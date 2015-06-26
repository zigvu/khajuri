import socket
import logging

class  ZFormatter(logging.Formatter):
  """Log formatter that respects ZFilter"""
  # Format as per issue 104
  # LOG Format:
  # [machine_hostname]::[zigvu_system]::[kheer_job_id]::[log_level]::
  # [date_time]::[file_name]::[line_number]::[process_id]::[message]
  # TIME Format:
  # [Year]-[Month]-[DAY]:[HOUR]-[MINUTE]-[SECOND]

  def __init__(self):
    """Init"""
    logging.Formatter.__init__(self)
    self.datefmt = '%Y-%m-%d:%H-%M-%S'

  def format(self, record):
    """Correctly formatted log"""
    msg = '%s' % (record.hostname)
    msg = '%s::%s' % (msg, record.name)
    msg = '%s::%s' % (msg, record.kheerjobid)
    msg = '%s::%s' % (msg, record.levelname)
    msg = '%s::%s' % (msg, self.formatTime(record, self.datefmt))
    msg = '%s::%s' % (msg, record.filename)
    msg = '%s::%s' % (msg, record.lineno)
    msg = '%s::%s' % (msg, record.process)
    msg = '%s::%s' % (msg, record.getMessage())
    return msg


class ZFilter(logging.Filter):
  """Specialized log filter to help in logging analytics"""
  def __init__(self, formatMsg):
    """Init"""
    logging.Filter.__init__(self)
    self.hostname = socket.gethostname()
    self.kheerjobid = 0
    if 'kheer_job_id' in formatMsg:
      self.kheerjobid = formatMsg['kheer_job_id']

  def filter(self, record):
    """Correctly formatted log"""
    record.hostname = self.hostname
    record.kheerjobid = self.kheerjobid
    return True


class ZLoggingStreamHandler(logging.StreamHandler):
  """Handler to write to std io"""
  def __init__(self):
    logging.StreamHandler.__init__(self)
    self.setFormatter(ZFormatter())



class ZLoggingQueueHandler(logging.Handler):
  """Handler to write to log queue"""
  def __init__(self, logQueue):
    logging.Handler.__init__(self)
    self.logQueue = logQueue

  def emit(self, record):
    """Write to queue"""
    self.logQueue.put(record)



class ZLoggingQueueProducer(object):
  """Produce logs from non-main process/threads"""
  def __init__(self, logQueue, logLevel, formatMsg):
    self.logger = logging.getLogger('zigvu.khajuri')
    self.logger.setLevel(logLevel)
    self.logger.addFilter(ZFilter(formatMsg))

    # remove existing handlers
    for handler in self.logger.handlers:
      assert not isinstance(handler, ZLoggingQueueHandler)
      self.logger.removeHandler(handler)
    # add the queue handler
    handler = ZLoggingQueueHandler(logQueue)
    self.logger.addHandler(handler)
    self.logger.propagate = False

  def getLogger(self):
    return self.logger



class ZLogging(object):
  def __init__(self, logLevel, formatMsg):
    self.logger = logging.getLogger('zigvu.khajuri')
    self.logger.setLevel(logLevel)
    self.logger.addFilter(ZFilter(formatMsg))

    handler = ZLoggingStreamHandler()
    self.logger.addHandler(handler)

  def getLogger(self):
    return self.logger
