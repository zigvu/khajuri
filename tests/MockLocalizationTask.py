from postprocessing.task.Task import Task
from postprocessing.task.Localization import Localization
from postprocessing.task.ClassFilter import ClassFilter
from tests.MockCaffeModel import MockCaffeModel
from tests.SingleFrameStatistics import SingleFrameStatistics
from postprocessing.type.Frame import Frame
import time

class MockLocalizationTask( Task ):
  def __init__( self, config, status ):
    Task.__init__( self, config, status )
    self.config = config
    self.status = status
    self.caffe = MockCaffeModel( self.config )
    self.localization = Localization( self.config, self.status )
    self.classFilter = ClassFilter( self.config, self.status )

  def __call__( self, annotatedFrame ):
    annotatedFrame.patchMapping = self.config.allCellBoundariesDict[ "patchMapping" ]
    annotatedFrame.frame = Frame(
            self.config.ci_allClassIds, len( annotatedFrame.patchMapping ),
            self.config.ci_scoreTypes.keys() )
    self.caffe.scoreFrame( annotatedFrame )
    #self.localization( self.classFilter( ( annotatedFrame.frame, self.config.ci_allClassIds ) ) )
    #singleFrameStat = SingleFrameStatistics( self.config.sw_frame_width,
    #    self.config.sw_frame_height, annotatedFrame )
    return annotatedFrame
