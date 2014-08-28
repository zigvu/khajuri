import glob, sys
import os, errno, math
import numpy as np
from skimage.transform import resize
import matplotlib.pyplot as plt

from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes
from Logo.PipelineMath.ScaleSpaceCombiner import ScaleSpaceCombiner
from Logo.PipelineMath.FramePostProcessor import FramePostProcessor
from Logo.PipelineMath.PixelMapper import PixelMapper
from Logo.PipelineMath.PixelMap import PixelMap

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.CurationManager import CurationManager
from Logo.PipelineCore.VideoWriter import VideoWriter

class TestPostProcessors(object):
  def __init__(self, configFileName, imageDim):
    self.configReader = ConfigReader(configFileName)
    self.imageDim = imageDim
    # initialize dimensions
    patchDimension = Rectangle.rectangle_from_dimensions(\
      self.configReader.sw_patchWidth, self.configReader.sw_patchHeight)
    self.staticBoundingBoxes = BoundingBoxes(imageDim, \
      self.configReader.sw_xStride, self.configReader.sw_xStride, patchDimension)

  def test_videoWriter(self, jsonFolder, imageFolder, outputFolder):
    """Test FramePostProcesor.py"""
    # TODO: dynamically populate fps from input video information
    fps = 1
    # we need frames in order
    frameIndex = {}
    jsonFiles = glob.glob(os.path.join(jsonFolder, "*json"))
    for jsonFileName in jsonFiles:
      print "Reading json " + os.path.basename(jsonFileName)
      jsonReaderWriter = JSONReaderWriter(jsonFileName)
      frameNumber = jsonReaderWriter.getFrameNumber()
      frameIndex[frameNumber] = jsonFileName
    print "Total of " + str(len(frameIndex.keys())) + " frames"
    classIds = JSONReaderWriter(jsonFiles[0]).getClassIds()
    # create video for each class - except background
    for classId in classIds:
      if classId in self.configReader.ci_backgroundClassIds:
        continue
      print "Working on video for class " + str(classId)
      videoFileName = os.path.join(outputFolder, "video_cls_" + str(classId) + ".avi")
      videoWriter = VideoWriter(videoFileName, fps, self.imageDim)
      for frameNumber in sorted(frameIndex.keys()):
        print "\tFrame number " + str(frameNumber)
        jsonReaderWriter = JSONReaderWriter(frameIndex[frameNumber])
        framePostProcessor = FramePostProcessor(jsonReaderWriter, self.staticBoundingBoxes, self.configReader)
        framePostProcessor.run()
        imageFileName = os.path.join(imageFolder, jsonReaderWriter.getFrameFileName())
        lclzPixelMap = framePostProcessor.classPixelMaps[classId]['localizationMap']
        imgLclz = ImageManipulator(imageFileName)
        imgLclz.addPixelMap(lclzPixelMap)
        for lclzPatch in jsonReaderWriter.getLocalizations(classId):
          bbox = Rectangle.rectangle_from_json(lclzPatch['bbox'])
          score = float(lclzPatch['score'])
          label = str(classId) + (": %.2f" % score)
          imgLclz.addLabeledBbox(bbox, label)
        videoWriter.addFrame(imgLclz)
      videoWriter.save()

  def test_curationManager(self, jsonFolder, imageFolder, outputFolder):
    """Test FramePostProcesor.py"""
    curationManager = CurationManager(jsonFolder, self.configReader)
    for frameNumber in curationManager.getFrameNumbers():
      for curationPatch in curationManager.getCurationPatches(frameNumber):
        bbox = Rectangle.rectangle_from_json(curationPatch['bbox'])
        patchFolderName = os.path.join(outputFolder, curationPatch['patch_foldername'])
        ConfigReader.mkdir_p(patchFolderName)
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
    for classId in jsonReaderWriter.getClassIds():
      if classId in self.configReader.ci_backgroundClassIds:
        continue
      scaleSpaceCombiner =  ScaleSpaceCombiner(classId, self.staticBoundingBoxes, jsonReaderWriter)
      # test PeaksExtractor.getPeakBboxes
      lclzPixelMap = scaleSpaceCombiner.getBestInferredPixelMap()
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
      intnPixelMap = scaleSpaceCombiner.getBestIntensityPixelMap()
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

    for classId in jsonReaderWriter.getClassIds():
      if classId in self.configReader.ci_backgroundClassIds:
        continue
      scaleSpaceCombiner =  ScaleSpaceCombiner(classId, self.staticBoundingBoxes, jsonReaderWriter)
      # test getBestInferredPixelMap
      lclzPixelMap = scaleSpaceCombiner.getBestInferredPixelMap()
      outputFileLclz = baseFileName + "_cls_" + str(classId) + "_bestInferred_lclz" + baseFileExt
      outputFileLclz = os.path.join(outputFolder, outputFileLclz)
      imgLclz = ImageManipulator(imageFileName)
      imgLclz.addPixelMap(lclzPixelMap)
      imgLclz.saveImage(outputFileLclz)
      # test getBestIntensityPixelMap
      intnPixelMap = scaleSpaceCombiner.getBestIntensityPixelMap()
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
    classIds = jsonReaderWriter.getClassIds()
    for classId in classIds:
      if classId in self.configReader.ci_backgroundClassIds:
        continue
      # since pixelMapper doesn't originally have inferred scales, use ScaleSpaceCombiner
      scaleSpaceCombiner =  ScaleSpaceCombiner(classId, self.staticBoundingBoxes, jsonReaderWriter)
      pixelMapper = scaleSpaceCombiner.pixelMapper
      for pm in pixelMapper.pixelMaps:
        scale = pm['scale']
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

  def test_single_pixelMap(self, allCellBoundariesDict, slidingWindowNum):
    scales = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4]
    scaleFactor = scales[2]
    print "Scale: %.2f" % scaleFactor
    pixelMap = PixelMap(allCellBoundariesDict, scaleFactor)
    pc = np.zeros((pixelMap.height, pixelMap.width))
    slidingWindows = self.staticBoundingBoxes.getBoundingBoxes(scaleFactor)
    counter = 0
    for slw in slidingWindows:
      y0 = slw[1]
      y3 = slw[1] + slw[3]
      x0 = slw[0]
      x3 = slw[0] + slw[2]
      score = 1
      if counter == slidingWindowNum:
        print "{x0: %d, y0: %d, x3: %d, y3: %d}" % (x0, y0, x3, y3) 
        pixelMap.addScore(x0, y0, x3, y3, score)
        pc[y0:y3, x0:x3] += score
        break
      counter += 1
    pm = pixelMap.toNumpyArray();
    return pm, pc
    

  def test_pixelMap(self, outputFolder, allCellBoundariesDict = None):
    """Test PixelMap.py"""
    scales = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4]
    if allCellBoundariesDict == None:
      allCellBoundariesDict = PixelMap.getCellBoundaries(self.staticBoundingBoxes, scales)

    celledPixelMaps = {}
    numpyPixelMaps = {}
    for idx, scaleFactor in enumerate(scales):
      # celled method
      celledPixelMap = PixelMap(allCellBoundariesDict, scaleFactor)
      # numpy method
      rect = self.staticBoundingBoxes.imageDim.get_scaled_rectangle(scaleFactor)
      numpyPixelMap = np.zeros((rect.height, rect.width))
      
      # populate pixel maps
      patchScore = 1
      slidingWindows = self.staticBoundingBoxes.getBoundingBoxes(scaleFactor)
      subplotNum = 0
      for slw in slidingWindows:
        y0 = slw[1] ; y3 = slw[1] + slw[3]
        x0 = slw[0] ; x3 = slw[0] + slw[2]
        # both methods
        celledPixelMap.addScore(x0, y0, x3, y3, patchScore)
        numpyPixelMap[y0:y3, x0:x3] += patchScore
      # save to dict
      celledPixelMaps[scaleFactor] = celledPixelMap.toNumpyArray()
      numpyPixelMaps[scaleFactor] = numpyPixelMap

    # make sure that all pixels got covered
    for scaleFactor in scales:
      cpm = celledPixelMaps[scaleFactor]
      npm = numpyPixelMaps[scaleFactor]
      cpmZero = np.count_nonzero(cpm == 0)
      npmZero = np.count_nonzero(npm == 0)
      if (cpmZero > 0) or (npmZero > 0):
        raise RuntimeError("One of the methods didn't populate all pixels")

    # check for area covered in each scale
    for scaleFactor in scales:
      cpm = celledPixelMaps[scaleFactor]
      npm = numpyPixelMaps[scaleFactor]
      uniqueCpm = np.unique(cpm)
      uniqueNpm = np.unique(npm)
      if len(uniqueCpm) != len(uniqueNpm):
        raise RuntimeError("Different number of unique pixels in two methods")
      for uniqueVal in uniqueCpm:
        cpmTotal = np.count_nonzero(cpm == uniqueVal)
        npmTotal = np.count_nonzero(npm == uniqueVal)
        print "Scale: %.2f, Value: %d, CelledCount: %d, NumpyCount: %d ;; Difference: %.4f%%" % (\
          scaleFactor, uniqueVal, cpmTotal, npmTotal, (1.0 * cpmTotal - npmTotal)/cpmTotal)

    # draw charts:
    fig = plt.figure(len(scales) + 1)
    for idx, scaleFactor in enumerate(scales):
      plt.subplot(len(scales), 3, idx * 3 + 1)
      im = plt.imshow(celledPixelMaps[scaleFactor])
      frame = plt.gca()
      frame.axes.get_xaxis().set_visible(False)
      frame.axes.get_yaxis().set_visible(False)
      plt.subplot(len(scales), 3, idx * 3 + 2)
      plt.imshow(numpyPixelMaps[scaleFactor])
      frame = plt.gca()
      frame.axes.get_xaxis().set_visible(False)
      frame.axes.get_yaxis().set_visible(False)
      plt.subplot(len(scales), 3, idx * 3 + 3)
      plt.imshow(celledPixelMaps[scaleFactor] - numpyPixelMaps[scaleFactor])
      frame = plt.gca()
      frame.axes.get_xaxis().set_visible(False)
      frame.axes.get_yaxis().set_visible(False)
    # save the plot
    plotFileName = os.path.join(outputFolder, "plot_allscales.png")
    # color bar is little misleading - so omit for now
    #cbar_ax = fig.add_axes([0.9, 0.15, 0.02, 0.7])
    #fig.colorbar(im, cbar_ax)
    fig.suptitle('CelledPixelMap, NumpyPixelMap, Difference', fontsize=12)
    plt.savefig(plotFileName)
    plt.close(fig)
    return celledPixelMaps, numpyPixelMaps

  def test_slidingWindows(self):
    """Test sliding window pixel calculations"""
    swScalesMin = 0.4
    swScalesMax = 3.0
    swScalesIncr = 0.1
    # original sliding windows
    for scale in np.arange(swScalesMin, swScalesMax, swScalesIncr):
      bboxes = self.staticBoundingBoxes.getBoundingBoxes(scale)
      maxX, maxY = 0, 0
      for bbox in bboxes:
        if maxX < (bbox[0] + bbox[2]):
          maxX = bbox[0] + bbox[2]
        if maxY < (bbox[1] + bbox[3]):
          maxY = bbox[1] + bbox[3]
        # print ("X: %d, Y: %d, W: %d, H: %d, X2: %d, Y2: %d" % 
        #   (bbox[0], bbox[1], bbox[2], bbox[3], bbox[0] + bbox[2], bbox[1] + bbox[3]))
      # test pixelMap shape
      pixelMapShape = np.shape(self.staticBoundingBoxes.pixelMapToRemoveDoubleCounting(scale))
      #print ("X: PM: %d, SW: %d; Y: PM: %d, SW: %d" % (pixelMapShape[1], maxX, pixelMapShape[0], maxY))
      if (pixelMapShape[1] != maxX) or (pixelMapShape[0] != maxY):
        raise RuntimeError("Sliding window and pixelMap creation don't match")
      # test zoom
      zoomMap = np.zeros(pixelMapShape)
      zoomedMapShape = np.shape(resize(zoomMap, (self.imageDim.height, self.imageDim.width)))
      # print ("X: Orig: %d, Zoom: %d; Y: Orig: %d, Zoom: %d" % 
      #   (self.imageDim.width, zoomedMapShape[1], self.imageDim.height, zoomedMapShape[0]))
      if (self.imageDim.width != zoomedMapShape[1]) or (self.imageDim.height != zoomedMapShape[0]):
        raise RuntimeError("PixelMap zoom don't match")
      print ("Scale: %0.2f - Pass" % scale)

