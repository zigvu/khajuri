import yaml, json, os
import snappy, StringIO
from collections import OrderedDict

class JSONReaderWriter( object ):
  def __init__( self, fileName, create_new = False ):
    self.fileName = fileName
    self.noPatchScores = False
    if not create_new:
      self.myDict = None
      accessFileName, accessFileExt = JSONReaderWriter.getCorrectFileName(self.fileName)
      if accessFileExt == ".snappy":
        iostr = StringIO.StringIO()
        snappy.stream_decompress( open( accessFileName, "rb" ), iostr )
        self.myDict = json.loads( iostr.getvalue() )
      elif accessFileExt == ".json":
        self.myDict = json.load( open( accessFileName, "r" ) )
      else:
        RuntimeError("File type not recognized %s" % self.fileName)

      # if patch scores are not present, this will be empty:
      if len(self.myDict[ 'scales' ]) == 0:
        self.noPatchScores = True
      else:
        self.scalingFactors = [ obj['scale'] for obj in self.myDict[ 'scales' ] ]

  def getAnnotationFileName( self ):
    return self.myDict[ 'annotation_filename' ]

  def getFrameFileName( self ):
    return self.myDict[ 'frame_filename' ]

  def getFrameNumber( self ):
    return self.myDict[ 'frame_number' ]

  def getFrameWidth( self ):
    return self.myDict[ 'frame_width' ]

  def getFrameHeight( self ):
    return self.myDict[ 'frame_height' ]

  def getScalingFactors( self ):
    self.checkScoreExists()
    return self.scalingFactors

  def getPatches( self, scale ):
    self.checkScoreExists()
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        return obj[ 'patches' ]

  def getPatchFileNames( self, scale ):
    self.checkScoreExists()
    fileNames = []
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        for patch in obj['patches']:
          fileNames.append( patch[ 'patch_filename' ] )
    return fileNames

  def getBoundingBoxes( self, scale ):
    self.checkScoreExists()
    boxes = []
    for obj in self.myDict[ 'scales' ]:
      if obj[ 'scale' ] == scale:
        for patch in obj['patches']:
          boxes.append( patch[ 'patch' ] )
    return boxes

  def getClassIds( self ):
    classIds = []
    # it might be possible to get classIds from localization
    # or curation even if no patch scores are saved
    if self.noPatchScores:
      if 'localizations' in self.myDict.keys():
        classIds = self.myDict['localizations'].keys()
      elif 'curations' in self.myDict.keys():
        classIds = self.myDict['curations'].keys()
    else:
      classIds = self.myDict['scales'][0]['patches'][0]['scores'].keys()
    if len(classIds) == 0:
      raise RuntimeError("Class ids cannot be determined for file %s" % self.fileName)
    return classIds

  def getScoreForPatchIdAtScale( self, patchId, classId, scale ):
    self.checkScoreExists()
    return self.myDict['scales'][ self.scalingFactors.index( scale ) ]['patches']\
        [patchId]['scores'][classId]

  def initializeJSON(self, videoId, frameId, imageDim, scales):
    self.videoId = videoId
    self.frameId = frameId
    self.myDict = OrderedDict()
    self.myDict[ 'annotation_filename' ] = '%s_frame_%s.json' % ( videoId, frameId )
    self.myDict[ 'frame_filename' ] = '%s_frame_%s.png' % ( videoId, frameId )
    self.myDict[ 'frame_number' ] = frameId
    self.myDict[ 'frame_width' ] = imageDim.width
    self.myDict[ 'frame_height' ] = imageDim.height
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
    for scaleVal in self.myDict['scales']:
      for patchVal in scaleVal['patches']:
        if leveldbCounter == int(patchVal['leveldb_counter']):
          patchVal['scores'] = scores
          return True
    return False
          
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

  def saveState( self, compressed_json = False, save_patch_scores = True ):
    # if we don't need to save patch scores, remove scales dict
    if save_patch_scores:
      self.checkScoreExists()
    else:
      self.myDict[ 'scales' ] = []

    # make sure we have the correct file extension
    fileToSave = self.fileName
    fileBasename, fileExt = os.path.splitext(self.fileName)
    if compressed_json:
      if not fileExt == ".snappy":
        fileToSave = "%s.snappy" % (self.fileName)
    else:
      if fileExt == ".snappy":
        fileToSave = fileBasename

    # dump json
    if compressed_json:
      with open( fileToSave, "wb" ) as f :
        iostr = StringIO.StringIO()
        json.dump( self.myDict, iostr, indent=2 )
        iostr.seek(0)
        snappy.stream_compress( iostr, f )
    else:
      with open( fileToSave, "w" ) as f :
        json.dump( self.myDict, f, indent=2 )

  def saveToCSV( self, csvFileName ):
    self.checkScoreExists()
    with open( csvFileName, "w" ) as f :
      topLineLabel = "Filename"
      classIds = self.getClassIds()
      for classId in classIds:
        topLineLabel = topLineLabel + ",Class_" + str(classId)
      f.write(topLineLabel + "\n")
      for obj in self.myDict[ 'scales' ]:
        for patch in obj['patches']:
          printStr = patch[ 'patch_filename' ]
          for classId in classIds:
            printStr = printStr + "," + repr(patch[ 'scores' ][ classId ])
          f.write(printStr + "\n")

  def checkScoreExists(self):
    """Raise exception if no patch scores are present"""
    if self.noPatchScores:
      raise RuntimeError("No patch scores saved in file %s" % self.fileName)
    else:
      return True

  @staticmethod
  def getCorrectFileName(fileName):
    """JSON files can now be stored as ".snappy" or ".json
    When either is supplied, transform to the right file extension
    based on what is available in the file system"""
    accessFileName = None
    accessFileExt = None
    fileBasename, fileExt = os.path.splitext(fileName)
    # check if file exists
    if os.path.isfile(fileName):
      # if file exists, then return extension and access file name
      accessFileName = fileName
      accessFileExt = fileExt
    else:
      # if file doesn't exist, then try another extension
      if fileExt == ".snappy":
        # if json file, then fileBasename must be JSON
        if os.path.isfile(fileBasename):
          fileBasenameTemp, fileExt = os.path.splitext(fileBasename)
          accessFileName = fileBasename
          accessFileExt = fileExt
      else:
        # if json file, then check to see if snappy
        fileNameTemp = "%s%s" % (fileName, ".snappy")
        if os.path.isfile(fileNameTemp):
          accessFileName = fileNameTemp
          accessFileExt = ".snappy"
    # error check
    if (accessFileName == None) or (accessFileExt == None):
      raise RuntimeError("File %s couldn't be read from disk" % fileName)
    # return values
    return accessFileName, accessFileExt
