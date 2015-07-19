from postprocessing.task.Task import Task
from postprocessing.task.ClassFilter import ClassFilter
from postprocessing.task.ZDistFilter import ZDistFilter
from postprocessing.task.Localization import Localization
from postprocessing.task.JsonWriter import JsonWriter
from postprocessing.task.RabbitWriter import RabbitWriter


class CaffeResultPostProcess(Task):

  def __init__(self, config, status):
    Task.__init__(self, config, status)
    self.storageCfg = self.config.storage
    _cellBoundaries = self.config.allCellBoundariesDict
    _neighborMap = self.config.neighborMap

    self.classFilter = ClassFilter(self.config, self.status),
    self.zDist = ZDistFilter(self.config, self.status),
    self.localization = Localization(self.config, self.status)
    self.frameSavers = []

  #@profile
  def __call__(self, obj):
    # allow for multiple writers
    if len(self.frameSavers) == 0:
      if self.storageCfg.enableJsonReadWrite:
        self.frameSavers += [JsonWriter(self.config, self.status)]
      if self.storageCfg.enableHdf5ReadWrite:
        self.frameSavers += [RabbitWriter(self.config, self.status)]

    classFilterResults = self.classFilter[0](obj)
    zDistResult = self.zDist[0](classFilterResults)
    localizationResult = self.localization(zDistResult)
    for frameSaver in self.frameSavers:
      frameSaver(localizationResult)
    # return (obj)
    self.logger.info("Frame Number: %d: Post-processed" % obj[0].frameNumber)
