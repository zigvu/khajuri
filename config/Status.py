class DebugFrame( object ):
  def __init__( self, frame ):
    self.frame = None
    self.hMap = {}
    self.lMap= {}

  def addHMap( self, heatMap, classId, scale, zDist ):
    self.hMap[ ( classId, scale, zDist ) ] = heatMap

  def addLMap( self, lMap, scale, zDist ):
    self.lMap[ ( classId, scale, zDist ) ] = lMap

class Status(object):
  def __init__( self, config ):
    self.config = config
    self.debugFrames = {}

  def addFrame( self, debugFrame ):
    self.debugFrames[ debugFrame.frame.frameNumber ] = debugFrame
