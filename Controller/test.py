#!/usr/bin/python

#TODO: fill wit more robust tests

import Config
from Common import CommonGroup
from Frame import FrameGroup
from Plugin import PluginGroup, BlankDetection, BlurDetection
from Result import ResultGroup
from DetectionStrand import DetectionStrand

# variables= {}
# execfile( "test.py", variables )
# variables['rg'].getNextResultToEvaluate().process()
# exit()

conf = Config.Config("config.yaml")

# Test FrameGroup:
print ""
print "#####-- Testing FrameGroup --#####"
fg = FrameGroup(4, conf)
# for f in fg:
# 	print f
print fg

print ""
print "#####-- Testing PluginGroup --#####"
pg = PluginGroup(conf)
# for p in pg:
# 	print p
print pg

print ""
print "#####-- Testing ResultGroup --#####"
rg = ResultGroup(fg, pg)
# for r in rg:
# 	print r
print rg

print ""
print "#####-- Testing DetectionStrand --#####"
ds = DetectionStrand(4, conf)
rg = ds.process()
print "After DetectionStrand"
print rg
