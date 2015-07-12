from config.Config import Config

class AnnotatedFrame( object ):
  def __init__( self, config ):
    self.classIds = config.ci_allClassIds
    self.config = config
    self.annotations = []
    self.patchMapping = None
    self.frame = None

  def addAnnotation( self, annotation ):
    self.annotations.append( annotation )

