from postprocessing.task.Task import Task
from postprocessing.task.Localization import Localization
from tests.MockCaffeModel import MockCaffeModel

class MockLocalizationTask( Task ):
  def __call__( self, annotatedFrame ):
    self.caffe = MockCaffeModel( self.config )
    self.localization = Localization( self.config, self.status )
    self.caffe.scoreFrame( annotatedFrame )
    self.localization( ( annotatedFrame.frame, self.config.ci_allClassIds ) )
    return annotatedFrame
