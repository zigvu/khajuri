class Task(object):

  def __init__(self, config, status):
    self.config = config
    self.status = status
    self.logger = self.status.logger

  def __str__(self):
    return str(self.__class__)
