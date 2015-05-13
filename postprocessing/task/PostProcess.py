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
from postprocessing.task.OldJsonReader import OldJsonReader
from postprocessing.task.Localization import Localization

class PostProcess( Task ):
  def __init__( self, config, status ):
    Task.__init__( self, config, status )
    self.reader = OldJsonReader( config, status ),
    self.classFilter = ClassFilter( config, status ),
    self.zDist = ZDistFilter( config, status ),
    self.localization = Localization( config, status )
    self.frameSaver = JsonWriter( config, status )

  #@profile
  def __call__( self, obj ):
    readerResults = self.reader[0]( obj )
    classFilterResults = self.classFilter[0]( readerResults )
    zDistResult = self.zDist[0]( classFilterResults )
    localizationResult = self.localization( zDistResult )
    self.frameSaver( localizationResult )
    return ( obj )
