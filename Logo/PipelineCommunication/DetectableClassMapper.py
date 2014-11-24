import sys, os, glob
import json, csv
from collections import OrderedDict
import logging

class DetectableClassMapper( object ):
  """Class to connect to cellroti and get detectable IDs"""
  def __init__(self):
    """Initialize values"""
    self.labeledMap = {}

  def read_mapped_detectables(self, inputFileName):
    """Once detectables have been matched to labels from caffe, load them"""
    logging.info("Loading detectable list file %s" % inputFileName)
    with open(inputFileName, "r") as f :
      reader = csv.reader(f)
      for idx, rows in enumerate(reader):
        if (idx > 0) and (rows[3] != ''):
          self.labeledMap[rows[3]] = rows[0]

  def get_mapped_caffe_label_ids(self):
    """Return all caffe label ids that have corresponding cellroti database ids"""
    return self.labeledMap.keys()

  def get_detectable_database_ids(self):
    """Return all cellroti database ids"""
    return self.labeledMap.values()

  def get_detectable_database_id(self, caffeLabelId):
    """Return the mapped cellroti database id for each caffe label mapped ID"""
    if not self.labeledMap:
      raise RuntimeError("Detectable mapped file not loaded")
    try:
      return self.labeledMap[("%s" % caffeLabelId)]
    except Exception, e:
      return None
    
  def save_detectable_list(self, outputFileName, detectableList):
    """Save jsonString into the outputFileName file"""
    logging.info("Saving detectable list file %s" % outputFileName)
    with open(outputFileName, "w") as f :
      topLineLabel = "id,name,pretty_name,label_mapping_id"
      f.write(topLineLabel + "\n")
      for detectable in detectableList:
        detectable_line = "%s,%s,%s," % (detectable["id"], detectable["name"], detectable["pretty_name"])
        f.write(detectable_line + "\n")


# ruby file copy:
# require 'fileutils'
# inputFolder = '/home/evan/WinMLVision/Videos/Logo/WorldCup/wc14-BraNed-HLTS/json-all'; outputFolder = '/home/evan/Vision/temp/sendto_cellroti/json'
# maxFrames = 100; Dir["#{inputFolder}/*"].each do |fn|; frameNum = File.basename(fn).split("_").last.split(".json").first.to_i; FileUtils.cp(fn, outputFolder) if frameNum < maxFrames; end; true
