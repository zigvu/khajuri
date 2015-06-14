import logging, json
import numpy as np
from Task import Task
from postprocessing.type.Frame import Frame
from postprocessing.type.Localization import Localization
from postprocessing.type.Rect import Rect

from config.Config import Config
from postprocessing.task.Task import Task
from postprocessing.task.ClassFilter import ClassFilter
from postprocessing.task.ZDistFilter import ZDistFilter
from postprocessing.task.JsonReader import JsonReader
from postprocessing.task.JsonWriter import JsonWriter
from postprocessing.task.RabbitWriter import RabbitWriter
from postprocessing.task.OldJsonReader import OldJsonReader
from postprocessing.task.Localization import Localization

class CaffeResultPostProcess( Task ):
  def __init__( self, config, status ):
    Task.__init__( self, config, status )
    self.classFilter = ClassFilter( config, status ),
    self.zDist = ZDistFilter( config, status ),
    self.localization = Localization( config, status )
    self.frameSavers = []

  #@profile
  def __call__( self, obj ):
    # allow for multiple writers
    if len(self.frameSavers) == 0:
      if self.config.pp_resultWriterJSON:
        self.frameSavers += [ JsonWriter( self.config, self.status ) ]
      if self.config.pp_resultWriterRabbit:
        self.frameSavers += [ RabbitWriter( self.config, self.status ) ]

    classFilterResults = self.classFilter[0]( obj )
    zDistResult = self.zDist[0]( classFilterResults )
    localizationResult = self.localization( zDistResult )
    for frameSaver in self.frameSavers:
      frameSaver( localizationResult )
    return ( obj )