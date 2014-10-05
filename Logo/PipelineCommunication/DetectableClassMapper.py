import sys, os, glob
from collections import OrderedDict
import logging, json

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter

class DetectableClassMapper( object ):
  """Class to extract data from caffe results to send to cellroti"""
  def __init__(self, videoFileName, jsonFolder, outputFileName, cellrotiDetectables):
    """Initialize values"""
    self.videoFileName = videoFileName
    self.jsonFolder = jsonFolder
    self.outputFileName = outputFileName
    self.cellrotiDetectables = cellrotiDetectables

  def run(self):
    """Create the json file to send to cellroti"""
    self.run_ffprobe(self.videoFileName)
    relabeldLocalizations = self.extract_localizations(self.jsonFolder, self.cellrotiDetectables)
    self.saveState(self.outputFileName, relabeldLocalizations)

  def run_ffprobe(self, videoFileName):
    """Run ffprobe and save video related information in JSON"""
    pass

  def extract_localizations(self, jsonFolder, cellrotiDetectables):
    """Extract localization for all classes in cellrotiDetectables from json folder"""
    relabeldLocalizations = OrderedDict()
    caffeLabelIds = cellrotiDetectables.get_mapped_caffe_label_ids()
    jsonFiles = glob.glob(os.path.join(jsonFolder, "*json"))
    for jsonFileName in jsonFiles:
      jsonReaderWriter = JSONReaderWriter(jsonFileName)
      frameNumber = jsonReaderWriter.getFrameNumber()
      relabeldLocalizations[frameNumber] = {}
      for caffeLabelId in caffeLabelIds:
        localizations = jsonReaderWriter.getLocalizations(caffeLabelId)
        if len(localizations) > 0:
          cellrotiDetectableId = cellrotiDetectables.get_detectable_database_id(caffeLabelId)
          relabeldLocalizations[frameNumber][cellrotiDetectableId] = localizations
    return relabeldLocalizations

  def saveState(self, outputFileName, outputDict):
    with open(outputFileName, "w") as f :
      json.dump(outputDict, f, indent=2 )

# ruby file copy:
# require 'fileutils'
# inputFolder = '/home/evan/WinMLVision/Videos/Logo/WorldCup/wc14-BraNed-HLTS/json-all'; outputFolder = '/home/evan/Vision/temp/sendto_cellroti/json'
# maxFrames = 1000; Dir["#{inputFolder}/*"].each do |fn|; frameNum = File.basename(fn).split("_").last.split(".json").first.to_i; FileUtils.cp(fn, outputFolder) if frameNum < maxFrames; end; true
