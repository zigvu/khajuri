import glob, sys
import os, errno

from Rectangle import Rectangle
from BoundingBoxes import BoundingBoxes
from ConfigReader import ConfigReader
from JSONReaderWriter import JSONReaderWriter
from PixelMapper import PixelMapper
from ImageManipulator import ImageManipulator
from ScaleSpaceCombiner import ScaleSpaceCombiner
from FramePostProcessor import FramePostProcessor
from CurationManager import CurationManager

class TestPostProcessors(object):
  def __init__(self, configFileName, imageDim):
    self.configReader = ConfigReader(configFileName)
    # initialize dimensions
    patchDimension = Rectangle.rectangle_from_dimensions(\
      self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    self.staticBoundingBoxes = BoundingBoxes(imageDim, \
      self.configReader.sw_xStride, self.configReader.sw_xStride, patchDimension)

  def test_curationManager(self, jsonFolder, imageFolder, outputFolder):
    """Test FramePostProcesor.py"""
    curationManager = CurationManager(jsonFolder, self.configReader)
    for frameNumber in curationManager.getFrameNumbers():
      for curationPatch in curationManager.getCurationPatches(frameNumber):
        bbox = curationPatch['bbox']
        patchFolderName = os.path.join(outputFolder, curationPatch['patch_foldername'])
        self.mkdir_p(patchFolderName)
        patchFileName = os.path.join(patchFolderName, curationPatch['patch_filename'])
        frameFileName = os.path.join(imageFolder, curationPatch['frame_filename'])
        imageManipulator = ImageManipulator(frameFileName)
        imageManipulator.extract_patch(bbox, patchFileName, \
          self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)

  def test_framePostProcessor(self, jsonFileName, imageFolder, outputFolder):
    """Test FramePostProcesor.py"""
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    imageFileName = os.path.join(imageFolder, jsonReaderWriter.getFrameFileName())
    baseFileName = os.path.splitext(os.path.basename(imageFileName))[0]
    baseFileExt = os.path.splitext(os.path.basename(imageFileName))[1]
    framePostProcessor = FramePostProcessor(jsonReaderWriter, self.staticBoundingBoxes, self.configReader)
    framePostProcessor.run()
    # also output heatmap
    scaleSpaceCombiner =  ScaleSpaceCombiner(self.staticBoundingBoxes, jsonReaderWriter)
    for classId in jsonReaderWriter.getClassIds():
      if classId in self.configReader.pp_backgroundClassIds:
        continue
      # test PeaksExtractor.getPeakBboxes
      lclzPixelMap = scaleSpaceCombiner.getBestInferredPixelMap(classId)
      outputFileLclz = baseFileName + "_cls_" + str(classId) + "_lclz" + baseFileExt
      outputFileLclz = os.path.join(outputFolder, outputFileLclz)
      imgLclz = ImageManipulator(imageFileName)
      imgLclz.addPixelMap(lclzPixelMap)
      for lclzPatch in jsonReaderWriter.getLocalizations(classId):
        bbox = Rectangle.rectangle_from_json(lclzPatch['bbox'])
        score = float(lclzPatch['score'])
        label = str(classId) + (": %.2f" % score)
        imgLclz.addLabeledBbox(bbox, label)
      imgLclz.saveImage(outputFileLclz)
      # test PeaksExtractor.getPatchesForCuration
      intnPixelMap = scaleSpaceCombiner.getBestIntensityPixelMap(classId)
      outputFileIntn = baseFileName + "_cls_" + str(classId) + "_curation" + baseFileExt
      outputFileIntn = os.path.join(outputFolder, outputFileIntn)
      imgIntn = ImageManipulator(imageFileName)
      imgIntn.addPixelMap(intnPixelMap)
      for curationPatch in jsonReaderWriter.getCurations(classId):
        bbox = Rectangle.rectangle_from_json(curationPatch['bbox'])
        score = float(curationPatch['score'])
        label = str(classId) + (": %.2f" % score)
        imgIntn.addLabeledBbox(bbox, label)
      imgIntn.saveImage(outputFileIntn)

  def test_scaleSpaceCombiner(self, jsonFileName, imageFolder, outputFolder):
    """Test ScaleSpaceCombiner.py"""
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    imageFileName = os.path.join(imageFolder, jsonReaderWriter.getFrameFileName())
    baseFileName = os.path.splitext(os.path.basename(imageFileName))[0]
    baseFileExt = os.path.splitext(os.path.basename(imageFileName))[1]

    scaleSpaceCombiner =  ScaleSpaceCombiner(self.staticBoundingBoxes, jsonReaderWriter)
    for classId in jsonReaderWriter.getClassIds():
      if classId in self.configReader.pp_backgroundClassIds:
        continue
      # test getBestInferredPixelMap
      lclzPixelMap = scaleSpaceCombiner.getBestInferredPixelMap(classId)
      outputFileLclz = baseFileName + "_cls_" + str(classId) + "_bestInferred_lclz" + baseFileExt
      outputFileLclz = os.path.join(outputFolder, outputFileLclz)
      imgLclz = ImageManipulator(imageFileName)
      imgLclz.addPixelMap(lclzPixelMap)
      imgLclz.saveImage(outputFileLclz)
      # test getBestIntensityPixelMap
      intnPixelMap = scaleSpaceCombiner.getBestIntensityPixelMap(classId)
      outputFileIntn = baseFileName + "_cls_" + str(classId) + "_bestInferred_intn" + baseFileExt
      outputFileIntn = os.path.join(outputFolder, outputFileIntn)
      imgIntn = ImageManipulator(imageFileName)
      imgIntn.addPixelMap(intnPixelMap)
      imgIntn.saveImage(outputFileIntn)

  def test_pixelMapper(self, jsonFileName, imageFolder, outputFolder):
    """Test PixelMapper.py"""
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    imageFileName = os.path.join(imageFolder, jsonReaderWriter.getFrameFileName())
    baseFileName = os.path.splitext(os.path.basename(imageFileName))[0]
    baseFileExt = os.path.splitext(os.path.basename(imageFileName))[1]
    # since pixelMapper doesn't originally have inferred scales, use ScaleSpaceCombiner
    scaleSpaceCombiner =  ScaleSpaceCombiner(self.staticBoundingBoxes, jsonReaderWriter)
    pixelMapper = scaleSpaceCombiner.pixelMapper
    for pm in pixelMapper.pixelMaps:
      classId = pm['classId']
      scale = pm['scale']
      if classId in self.configReader.pp_backgroundClassIds:
        continue
      # test localization
      localizationMap = pm['localizationMap']
      outputFileLclz = baseFileName + "_cls_" + str(classId) + "_scl_" + str(scale) + "_lclz" + baseFileExt
      outputFileLclz = os.path.join(outputFolder, outputFileLclz)
      imgLclz = ImageManipulator(imageFileName)
      imgLclz.addPixelMap(localizationMap)
      imgLclz.saveImage(outputFileLclz)
      # test intensity
      intensityMap = pm['intensityMap']
      outputFileIntn = baseFileName + "_cls_" + str(classId) + "_scl_" + str(scale) + "_intn" + baseFileExt
      outputFileIntn = os.path.join(outputFolder, outputFileIntn)
      imgIntn = ImageManipulator(imageFileName)
      imgIntn.addPixelMap(intensityMap)
      imgIntn.saveImage(outputFileIntn)

  def mkdir_p(self, path):
    """Util to make path"""
    try:
      os.makedirs(path)
    except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST and os.path.isdir(path):
        pass


if __name__ == '__main__':
  if len(sys.argv) < 6:
    print 'Usage %s <config.yaml> <testMode> <jsonFolder> <imageFolder> <outputFolder>' % sys.argv[ 0 ]
    print 'Test modes (integer):'
    print '\t1: Test PixelMapper\n\t2: Test ScaleSpaceCombiner\n\t3: Test FramePostProcessor'
    print '\t4: Test CurationManager\n'
    sys.exit(1)

  configFileName = sys.argv[1]
  testMode = int(sys.argv[2])
  jsonFolder = sys.argv[3]
  imageFolder = sys.argv[4]
  outputFolder = sys.argv[5]
  # TODO: replace from video frame information
  imageDim = Rectangle.rectangle_from_dimensions(1280, 720)
  testPostProcessors = TestPostProcessors(configFileName, imageDim)
  jsonFiles = glob.glob(os.path.join(jsonFolder, "*json"))
  if (testMode == 1) or (testMode == 2) or (testMode == 3):
    for jsonFileName in jsonFiles:
      print "Working on " + os.path.basename(jsonFileName)
      if testMode == 1:
        testPostProcessors.test_pixelMapper(jsonFileName, imageFolder, outputFolder)
      elif testMode == 2:
        testPostProcessors.test_scaleSpaceCombiner(jsonFileName, imageFolder, outputFolder)
      elif testMode == 3:
        testPostProcessors.test_framePostProcessor(jsonFileName, imageFolder, outputFolder)
  elif (testMode == 4):
    testPostProcessors.test_curationManager(jsonFolder, imageFolder, outputFolder)

