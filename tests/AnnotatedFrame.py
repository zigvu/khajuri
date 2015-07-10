from config.Config import Config
from postprocessing.type.Frame import Frame

class AnnotatedFrame( object ):
  def __init__( self, config ):
    self.classIds = config.ci_allClassIds
    self.config = config
    self.cellBoundariesDict = config.allCellBoundariesDict
    self.patchMapping = self.cellBoundariesDict[ "patchMapping" ]
    self.frame = Frame(
            self.classIds, len( self.patchMapping ),
            self.config.ci_scoreTypes.keys() )
    self.annotations = []

  def addAnnotation( self, annotation ):
    self.annotations.append( annotation )

