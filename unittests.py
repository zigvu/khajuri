#!/usr/bin/python
import VideoPipeline
import Config
from Frame import FrameGroup
from Plugin import PluginGroup, BlankDetection, BlurDetection
from Result import ResultGroup
from DetectionStrand import DetectionStrand, DetectionStrandGroup
import unittest
import VideoReader

class TestVideoPipelin(unittest.TestCase):
 
    def setUp(self):
        self.configFileName = 'config.yaml'
        self.videoFileName = "/home/regmi/commercial.mp4"
	self.conf = Config.Config( self.configFileName )
	self.fg = None
	self.pg = None
    
    def testFrameGroup(self):
        # Test FrameGroup:
        print "#####-- Testing FrameGroup --#####"
        self.fg = FrameGroup(4, self.conf)
        print fg

    def testPluginGroup(self):
        print "#####-- Testing PluginGroup --#####"
        self.pg = PluginGroup(self.conf)
        print pg
    
    def testResultGroup(self):
        print "#####-- Testing ResultGroup --#####"
        rg = ResultGroup(self.fg, self.pg)
        print rg

    def testDetectionStrand(self):
        print "#####-- Testing DetectionStrand --#####"
        ds = DetectionStrand(4, self.conf)
        rg = ds.process()
        print rg

    def testVideoReader(self):
        myFrameReader = VideoReader.VideoFrameReader( 40, 40, self.videoFileName )
        print myFrameReader.fps
        print myFrameReader.lengthInMicroSeconds
        myFrameReader.generateFrames()
        vFrame = True
        i = 1
        while not myFrameReader.eof:
           vFrame = myFrameReader.getFrameWithFrameNumber( i )
           if vFrame:
             i += 1
             print 'TimeStamp: %s' % vFrame.timeStamp
             print 'FrameNum: %s' % vFrame.frameNum
        myFrameReader.waitForEOF()       

    def testDetectionStrandGroup(self):
        dsg = DetectionStrandGroup( self.videoFileName, self.conf )
	dsg.runVidPipe()
    
    def testVideoPipeline(self):
         VideoPipeline.processVideo( self.configFileName, self.videoFileName )
 
if __name__ == '__main__':
    unittest.main()
