class PatchMapper( object ):
  def __init__( self ):
    self.myIds = {}
    self.nextId = 0
    self.patchIdsAtScale = {}

  def patchId( self, scale, rect ):
    if not self.myIds.get( ( scale, rect ) ):
       self.myIds [ ( scale, rect ) ] = self.nextId
    if not self.patchIdsAtScale.get( scale ):
      self.patchIdsAtScale[ scale ] = []
    self.patchIdsAtScale[ scale ].append( self.nextId )
    self.nextId += 1
    return self.myIds[ ( scale, rect ) ]
