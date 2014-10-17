import glob, os
from operator import itemgetter

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter

class CurationManager(object):
  def __init__(self, inputJSONFolder, configReader):
    """Initialize values"""
    self.inputJSONFolder = inputJSONFolder
    self.curationNumOfItemsPerSet = configReader.cr_curationNumOfItemsPerSet
    self.curationNumOfSets = configReader.cr_curationNumOfSets

    # extract JSONs and compute bboxes
    self.classIds, self.frameNumbers, self.curationBboxes, self.localizationBboxes = self.extractFromJSONFiles()
    self.curation_patches = None

  def getCurationFrames(self, classId):
    """Aggregate curations at frame level for a class"""
    # initialize container to hold final curation boxes
    frameIndex = {}
    for frameNumber in self.frameNumbers:
      frameIndex[frameNumber] = []
    # sort (in ascending order) curations for whole class based on scores
    sortedCurationBboxes = sorted(self.curationBboxes[classId], \
      key = itemgetter('score'))
    # becase scores are sorted, smaller scores will be overwritten
    # with larger scores
    for curation in sortedCurationBboxes:
      frameIndex[curation['frame_number']] = curation
    # reorganize frames based on scores
    curationFrames = []
    for frameNumber, curation in frameIndex.iteritems():
      if curation != []:
        baseFrameFileName = os.path.basename(curation['frame_filename'])
        frameFileName = ("%.4f_cls_%s_" % (curation['score'], str(classId))) + baseFrameFileName
        curationFrames += [{ \
          'frame_number': frameNumber, \
          'score': curation['score'], \
          'frame_filename': frameFileName, \
          'set_number': None}]
    # put frames in sets
    curationFrames = sorted(curationFrames, key = itemgetter('score'), reverse = True)
    setId = -1
    for idx, curation in enumerate(curationFrames):
      # stopping conditions
      if (idx % self.curationNumOfItemsPerSet) == 0:
        setId += 1
      if setId >= self.curationNumOfSets:
        break
      curation['set_number'] = setId
      curation['frame_foldername'] = os.path.join(("set_%d" % setId), "class_" + str(classId))
    # organize curations based on frame numbers for easy access
    frameIndex = {}
    for frameNumber in sorted(self.frameNumbers):
      for curation in curationFrames:
        if (curation['set_number'] != None) and (curation['frame_number'] == frameNumber):
          frameIndex[frameNumber] = { \
            'frame_filename': str(curation['frame_filename']), \
            'frame_foldername': str(curation['frame_foldername'])}
    return frameIndex

  def getFrameNumbers(self):
    """Get frame numbers of all frames from which to extract patches"""
    return sorted(self.frameNumbers)

  def getCurationPatches(self, frameNumber):
    """For a frame number, get all patches that need to be generated
    Returns: Array of {bbox, patch_foldername, patch_filename}
    """
    if self.curation_patches is None:
      self.curation_patches = self.aggregateCurationPatches()
    return self.curation_patches[frameNumber]

  def getDetectionCount(self, frameNumber, classId):
    """For a frame number get the count of bboxes above threshold defined
    in configReader."""
    return len(self.localizationBboxes[frameNumber][classId])

  def aggregateCurationPatches(self):
    """Aggregate curations for each frame"""
    # initialize container to hold final curation boxes
    frameIndex = {}
    for frameNumber in self.frameNumbers:
      frameIndex[frameNumber] = []
    # sort curations for whole class based on scores
    for classId in self.classIds:
      self.curationBboxes[classId] = sorted(self.curationBboxes[classId], \
        key = itemgetter('score'), reverse = True)
      # assign each curation a set_number
      setId = -1
      for idx, curation in enumerate(self.curationBboxes[classId]):
        # stopping conditions
        if (idx % self.curationNumOfItemsPerSet) == 0:
          setId += 1
        if setId >= self.curationNumOfSets:
          break
        curation['set_number'] = setId
        curation['patch_foldername'] = os.path.join(("set_%d" % setId), "class_" + str(classId))
    # organize curations based on frame numbers for easy access
    for frameNumber in sorted(frameIndex.keys()):
      for classId in self.classIds:
        for curation in self.curationBboxes[classId]:
          if (curation['set_number'] != None) and (curation['frame_number'] == frameNumber):
            frameIndex[frameNumber] += [{'bbox': curation['bbox'], \
              'patch_foldername': curation['patch_foldername'], \
              'patch_filename': curation['patch_filename'],\
              'frame_filename': curation['frame_filename']}]
    return frameIndex

  def extractFromJSONFiles(self):
    """Read JSON files and construct curationBboxes dictionary"""
    # read json files
    jsonFiles = glob.glob(os.path.join(self.inputJSONFolder, "*json"))
    if len(jsonFiles) <= 0:
      raise IOError("JSON folder doesn't have any json files")
    classIds = JSONReaderWriter(jsonFiles[0]).getClassIds()
    frameNumbers = []
    # extract all curations
    curationBboxes = {}
    for classId in classIds:
      curationBboxes[classId] = []
    # extract all localizations
    localizationBboxes = {}
    for f in jsonFiles:
      reader = JSONReaderWriter(f)
      frameNumber = reader.getFrameNumber()
      frameNumbers += [frameNumber]
      frameFileName = reader.getFrameFileName()
      baseFrameFileName = os.path.basename(frameFileName)
      localizationBboxes[frameNumber] = {}
      for classId in classIds:
        # Read curations from JSON
        curations = sorted(reader.getCurations(classId), key = itemgetter('score'), reverse = True)        
        for idx, curation in enumerate(curations):
          bbox = curation['bbox']
          score = float(curation['score'])
          patchFileName = ("%.4f_cls_%s_cur_%d_" % (score, str(classId), idx)) + baseFrameFileName
          curationBboxes[classId] += [{'frame_number': frameNumber, \
            'bbox': bbox, 'score': score, 'patch_filename': patchFileName, \
            'frame_filename': frameFileName,'set_number': None}]
        # Read localizations from JSON
        localizations = sorted(reader.getLocalizations(classId), key = itemgetter('score'), reverse = True)
        localizationBboxes[frameNumber][classId] = []
        for idx, localization in enumerate(localizations):
          bbox = localization['bbox']
          score = float(localization['score'])
          #patchFileName = ("%.4f_loc_%d_cls_%s_" % (score, idx, str(classId))) + baseFrameFileName
          patchFileName = ("%.4f_cls_%s_loc_%d_" % (score, str(classId), idx)) + baseFrameFileName
          localizationBboxes[frameNumber][classId] += [{'frame_number': frameNumber, \
            'bbox': bbox, 'score': score, 'patch_filename': patchFileName, \
            'frame_filename': frameFileName}]        
    return classIds, frameNumbers, curationBboxes, localizationBboxes
