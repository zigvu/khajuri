import os
import yaml

from config.config_manager.Environments import Environments

from config.config_manager.Jobs import Jobs
from config.config_manager.Machines import Machines
from config.config_manager.Loggers import Loggers
from config.config_manager.Messaging import Messaging
from config.config_manager.Storage import Storage

from config.config_manager.Pipeline import SlidingWindow
from config.config_manager.Pipeline import CaffeInput
from config.config_manager.Pipeline import PostProcessing

from Logo.PipelineMath.PixelMap import CellBoundaries
from Logo.PipelineMath.PixelMap import NeighborsCache


class Config:
  """Reads YAML config file and allows easy accessor to config attributes"""

  def __init__(self, configFileName):
    """Initlize config from YAML file"""
    self.configHash = yaml.load(open(configFileName, "r"))
    self.configHash.update({
      'config_root_folder': os.path.dirname(configFileName)
    })

    # khajuri configs
    self._environment = None
    self._job = None
    self._machine = None
    self._logging = None
    self._messaging = None
    self._storage = None
    self._slidingWindow = None
    self._caffeInput = None
    self._postProcessing = None

    # cell boundaries and neighbor maps
    self._allCellBoundariesDict = None
    self._neighborMap = None


  @property
  def environment(self):
    if not self._environment:
      self._environment = Environments(self.configHash).environment
    return self._environment

  @property
  def job(self):
    if not self._job:
      jobType = self.configHash['execution']['job']
      self._job = Jobs(self.configHash, jobType)
    return self._job

  @property
  def machine(self):
    if not self._machine:
      mType = self.configHash['execution']['machine']
      self._machine = Machines(self.configHash, mType)
    return self._machine

  @property
  def logging(self):
    if not self._logging:
      logExtraParams = {'environment': self.environment}
      logExtraParams.update(self.job.getLogExtraParams())
      self._logging = Loggers(self.configHash, logExtraParams)
    return self._logging

  @property
  def messaging(self):
    if not self._messaging:
      if self.environment == Environments.LOCAL:
        raise RuntimeError("No queue specified for local environment")
      else:
        self._messaging = Messaging(self.configHash, self.environment)
    return self._messaging

  @property
  def storage(self):
    if not self._storage:
      self._storage = Storage(self.configHash)
    return self._storage

  @property
  def slidingWindow(self):
    if not self._slidingWindow:
      self._slidingWindow = SlidingWindow(self.configHash)
    return self._slidingWindow

  @property
  def caffeInput(self):
    if not self._caffeInput:
      self._caffeInput = CaffeInput(self.configHash)
    return self._caffeInput

  @property
  def postProcessing(self):
    if not self._postProcessing:
      self._postProcessing = PostProcessing(self.configHash)
    return self._postProcessing

  @property
  def allCellBoundariesDict(self):
    if not self._allCellBoundariesDict:
      self._allCellBoundariesDict = CellBoundaries(self).allCellBoundariesDict
    return self._allCellBoundariesDict

  @property
  def neighborMap(self):
    if not self._neighborMap:
      neighborCache = NeighborsCache(self)
      self._neighborMap = neighborCache.neighborMapAllScales(
          self.allCellBoundariesDict)
    return self._neighborMap
