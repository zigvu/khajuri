import glob, os
from operator import itemgetter

from JSONReaderWriter import JSONReaderWriter

class CurationManager(object):
  def __init__(self, inputJSONFolder, configReader):
    """Initialize values"""
    self.inputJSONFolder = inputJSONFolder
    self.curationNumOfPatchPerSet = configReader.cr_curationNumOfPatchPerSet
    self.curationNumOfSets = configReader.cr_curationNumOfSets
    self.curation_patches = self.aggregateCurationPatches()

  def getFrameNumbers(self):
    """Get frame numbers of all frames from which to extract patches"""
    return sorted(self.curation_patches.keys())

  def getCurationPatches(self, frameNumber):
    """For a frame number, get all patches that need to be generated
    Returns: Array of {bbox, patch_foldername, patch_filename}
    """
    return self.curation_patches[frameNumber]


  def aggregateCurationPatches(self):
    """From all input JSON files, extract the curation boxes and scores"""
    # read json files
    jsonFiles = glob.glob(os.path.join(self.inputJSONFolder, "*json"))
    if len(jsonFiles) <= 0:
      raise IOError("JSON folder doesn't have any json files")
    classIds = JSONReaderWriter(jsonFiles[0]).getClassIds()
    frameIndex = {}
    # extract all curations
    curationBboxes = {}
    for classId in classIds:
      curationBboxes[classId] = []
    for f in jsonFiles:
      reader = JSONReaderWriter(f)
      frameNumber = reader.getFrameNumber()
      # initialize container to hold final curation boxes
      frameIndex[frameNumber] = []
      frameFileName = reader.getFrameFileName()
      baseFrameFileName = os.path.splitext(os.path.basename(frameFileName))[0]
      baseFrameFileExt = os.path.splitext(os.path.basename(frameFileName))[1]
      for classId in classIds:
        curations = sorted(reader.getCurations(classId), key = itemgetter('score'), reverse = True)
        for idx, curation in enumerate(curations):
          bbox = curation['bbox']
          score = float(curation['score'])
          patchFileName = baseFrameFileName + ("_cur_%d_%.2f" % (idx, score)) + baseFrameFileExt
          curationBboxes[classId] += [{'frame_number': frameNumber, \
            'bbox': bbox, 'score': score, 'patch_filename': patchFileName, \
            'frame_filename': frameFileName,'set_number': None}]
    # sort curations for whole class based on scores
    for classId in classIds:
      curationBboxes[classId] = sorted(curationBboxes[classId], key = itemgetter('score'), reverse = True)
      # assign each curation a set_number
      setId = -1
      for idx, curation in enumerate(curationBboxes[classId]):
        # stopping conditions
        if (idx % self.curationNumOfPatchPerSet) == 0:
          setId += 1
        if setId >= self.curationNumOfSets:
          break
        curation['set_number'] = setId
        curation['patch_foldername'] = os.path.join(("set_%d" % setId), "class_" + str(classId))
    # organize curations based on frame numbers for easy access
    for frameNumber in sorted(frameIndex.keys()):
      for classId in classIds:
        for curation in curationBboxes[classId]:
          if (curation['set_number'] != None) and (curation['frame_number'] == frameNumber):
            frameIndex[frameNumber] += [{'bbox': curation['bbox'], \
              'patch_foldername': curation['patch_foldername'], \
              'patch_filename': curation['patch_filename'],\
              'frame_filename': curation['frame_filename']}]
    return frameIndex
