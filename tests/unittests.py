#!/usr/bin/python
import unittest
import random, os, subprocess
import tempfile, shutil

from postprocessing.type.Frame import Frame
from postprocessing.task.JsonWriter import JsonWriter
from config.Config import Config
from config.Status import Status
from config.Version import Version

from Logo.PipelineMath.PixelMap import PixelMap
from Logo.PipelineMath.Rectangle import Rectangle
from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

from tool import pp

baseScriptDir = os.path.dirname(os.path.realpath(__file__))


class TestVersion(unittest.TestCase):

  def testVersion(self):
    v = Version()
    branch, commit = v.getGitVersion()
    print "Branch: %s" % branch
    print "Commit: %s" % commit

class TestFrameInfo(unittest.TestCase):

  def testBasic(self):
    frame = Frame([1, 2, 3], 543, [0, 1])

    # Basic Setting of Frame
    frame.frameNumber = 3
    frame.frameDisplayTime = 10000

    assert frame.frameNumber == 3
    assert frame.frameDisplayTime == 10000

  def testScores(self):
    frame = Frame([1, 2, 3], 543, [0, 1])

  def testLocalization(self):
    pass

  def testCurations(self):
    frame = Frame([1, 2, 3], 543, [0, 1])
    config = Config(baseScriptDir + os.sep + 'config.yaml')
    logger = config.logging.logger

    status = Status(logger)
    frameJsonWriter = JsonWriter(config, status)
    frameJsonWriter((frame, '/tmp/save.json'))

  def testPickle(self):
    frame = Frame([1, 2, 3], 543, [0, 1])
    pass


class PixelMapTest(unittest.TestCase):

  def testNeighborMap(self):
    return
    ''' Test NeighborMap created '''
    xStepSize = {0.4: 32, 1: 32, 1.4: 32,}
    yStepSize = {0.4: 32, 1: 32, 1.4: 32,}
    scales = [0.4, 0.7, 1.0, 1.3, 1.6]
    staticBoundingBoxes = BoundingBoxes(
        1280, 720, xStepSize, yStepSize, 256, 256, scales)
    allCellBoundariesDict = PixelMap.getCellBoundaries(
        staticBoundingBoxes, [0.4, 1, 1.4])

  def testCellMap(self):
    ''' Test the cellMap created '''
    pass


class TestPipeline(unittest.TestCase):

  def testPipeline(self):
    ''' Test running the pp pipeline '''
    configFile = baseScriptDir + os.sep + "config.yaml"
    jsonFolder = tempfile.mkdtemp()
    sampleJsonFile = baseScriptDir + os.sep + "sample.json"
    for i in range(100):
      shutil.copyfile(sampleJsonFile,
                      jsonFolder + os.sep + "sample_%d.json" % i)
    pp.process(configFile, jsonFolder)
    shutil.rmtree(jsonFolder)


if __name__ == '__main__':
  unittest.main()
