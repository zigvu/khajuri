import yaml, json
from collections import OrderedDict

class JSONReaderWriter( object ):
  def __init__( self, fileName, create_new = False ):
    self.fileName = fileName
    if not create_new:
      self.myDict = json.load( open( fileName, "r" ) )
      self.scalingFactors = [ obj['scale'] for obj in self.myDict[ 'scales' ] ]

  def getAnnotationFileName( self ):
    return self.myDict[ 'annotation_filename' ]

  def getFrameFileName( self ):
    return self.myDict[ 'frame_filename' ]

  def getFrameNumber( self ):
    return self.myDict[ 'frame_number' ]

  def getScalingFactors( self ):
    return self.scalingFactors

  def getPatches( self, scale ):
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        return obj[ 'patches' ]

  def getPatchFileNames( self, scale ):
    fileNames = []
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        for patch in obj['patches']:
          fileNames.append( patch[ 'patch_filename' ] )
    return fileNames

  def getBoundingBoxes( self, scale ):
    boxes = []
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        for patch in obj['patches']:
          boxes.append( patch[ 'patch' ] )
    return boxes

  def getClassIds( self ):
    return self.myDict['scales'][0]['patches'][0]['scores'].keys()

  def getScoreForPatchIdAtScale( self, patchId, classId, scale ):
    return self.myDict['scales'][ self.scalingFactors.index( scale ) ]['patches']\
        [patchId]['scores'][classId]

  def initializeJSON(self, videoId, frameId, scales):
    self.videoId = videoId
    self.frameId = frameId
    self.myDict = OrderedDict()
    self.myDict[ 'annotation_filename' ] = '%s_frame_%s.json' % ( videoId, frameId )
    self.myDict[ 'frame_filename' ] = '%s_frame_%s.png' % ( videoId, frameId )
    self.myDict[ 'frame_number' ] = frameId
    self.myDict[ 'scales' ] = []
    for scale in scales:
      self.myDict[ 'scales' ].append(OrderedDict(\
        [('scale', scale), ('patches', [])]))

  def addPatch(self, scale, patchNum, leveldbCounter, x, y, width, height):
    for scaleVal in self.myDict['scales']:
      if scaleVal['scale'] == scale:
        scaleVal['patches'].append(OrderedDict(\
          [('patch_filename' , 
            '%s_frame_%s_scl_%s_idx_%s.png' % (self.videoId, self.frameId, scale, patchNum)),
          ('patch', OrderedDict([('x', x), ('y', y), ('width', width), ('height', height)])),
          ('leveldb_counter', leveldbCounter)]))

  def addScores(self, leveldbCounter, scores):
    setBreak = False
    for scaleVal in self.myDict['scales']:
      if setBreak: break
      for patchVal in scaleVal['patches']:
        if setBreak: break
        if leveldbCounter == int(patchVal['leveldb_counter']):
          patchVal['scores'] = scores
          setBreak = True
          
  def initializeLocalizations( self ):
    if not 'localizations' in self.myDict.keys():
      self.myDict['localizations'] = OrderedDict()
    # if localizations exist from previous runs, clean up
    for clsId in self.getClassIds():
      self.myDict['localizations'][clsId] = []

  def getLocalizations( self, classId ):
    return self.myDict['localizations'][classId]

  def addLocalization( self, classId, bbox, score ):
    self.myDict['localizations'][classId] += [{'bbox': bbox, 'score': score}]

  def initializeCurations( self ):
    if not 'curations' in self.myDict.keys():
      self.myDict['curations'] = OrderedDict()
    # if curations exist from previous runs, clean up
    for clsId in self.getClassIds():
      self.myDict['curations'][clsId] = []

  def getCurations( self, classId ):
    return self.myDict['curations'][classId]

  def addCuration( self, classId, bbox, score ):
    self.myDict['curations'][classId] += [{'bbox': bbox, 'score': score}]

  def saveState( self ):
    with open( self.fileName, "w" ) as f :
      json.dump( self.myDict, f, indent=2 )
