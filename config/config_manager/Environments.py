
class Environments(object):
  """Sets up messaging related configs"""
  # declare constants
  LOCAL = 'local'
  DEVELOPMENT = 'development'
  PRODUCTION = 'production'

  def __init__(self, configHash):
    """Initialize variables"""
    envType = configHash['execution']['environment']
    self.environment = None
    if envType == Environments.LOCAL:
      self.environment = Environments.LOCAL
    elif envType == Environments.DEVELOPMENT:
      self.environment = Environments.DEVELOPMENT
    elif envType == Environments.PRODUCTION:
      self.environment = Environments.PRODUCTION
    else:
      raise RuntimeError("Environment type not recognized: %s" % envType)
