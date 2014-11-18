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
    # TODO: get from config
    self.detectionFrameRate = 5
    self.numSecondsForSingleFrameSaved = 10

  def run(self):
    """Create the json file to send to cellroti"""
    ffprobeResults = self.run_ffprobe(self.videoFileName)
    relabeledLocalizations = self.extract_localizations(self.jsonFolder, self.cellrotiDetectables)
    saveJSON = {
      'video_id': 1,
      'video_attributes': ffprobeResults,
      'detections': relabeledLocalizations,
    }
    self.save_state(self.outputFileName, saveJSON)

  def run_ffprobe(self, videoFileName):
    """Run ffprobe and save video related information in JSON"""
    ffprobeResults = {
      'quality': "high",
      'format': "mp4",
      'length': 102300,
      'width': 1280,
      'height': 720,
      'detection_frame_rate': self.detectionFrameRate, # <-- this implies 5 frames evaluated in 1 second, regardless of playback_frame_rate
      'playback_frame_rate': 25  # <-- this implies 25 frames played in 1 second
    }
    return ffprobeResults

  def extract_localizations(self, jsonFolder, cellrotiDetectables):
    """Extract localization for all classes in cellrotiDetectables from json folder"""
    relabeledLocalizations = OrderedDict()
    caffeLabelIds = cellrotiDetectables.get_mapped_caffe_label_ids()
    jsonFiles = glob.glob(os.path.join(jsonFolder, "*json"))
    for jsonFileName in jsonFiles:
      jsonReaderWriter = JSONReaderWriter(jsonFileName)
      frameNumber = jsonReaderWriter.getFrameNumber()
      relabeledLocalizations[frameNumber] = {}
      for caffeLabelId in caffeLabelIds:
        localizations = jsonReaderWriter.getLocalizations(caffeLabelId)
        if len(localizations) > 0:
          cellrotiDetectableId = cellrotiDetectables.get_detectable_database_id(caffeLabelId)
          relabeledLocalizations[frameNumber][cellrotiDetectableId] = localizations
    relabeledLocalizations = OrderedDict(sorted(relabeledLocalizations.items(), key=lambda t: t[0]))
    return relabeledLocalizations

  def add_frame_numbers(self, relabeledLocalizations, cellrotiDetectables):
    numFrameIntervalPerFrameSaved = self.numSecondsForSingleFrameSaved * self.detectionFrameRate
    cellrotiDetectableIds = cellrotiDetectables.get_detectable_database_ids()
    frameTrackers = {}
    # init frame counters
    for cellrotiDetectableId in cellrotiDetectableIds:
      frameTrackers[cellrotiDetectableId] = {
        'counter': 0,
        'maxScore': -1.0,
        'maxScoreFrameNum': -1
      }
    # loop through all frame localizations and find right frames
    for frameNum in relabeledLocalizations:
      # increase counters
      print "%d" % frameNum

    return frameTrackers


  def save_state(self, outputFileName, outputDict):
    with open(outputFileName, "w") as f :
      json.dump(outputDict, f, indent=2 )

# ruby file copy:
# require 'fileutils'
# inputFolder = '/home/evan/WinMLVision/Videos/Logo/WorldCup/wc14-BraNed-HLTS/json-all'; outputFolder = '/home/evan/Vision/temp/sendto_cellroti/json'
# maxFrames = 500; Dir["#{inputFolder}/*"].each do |fn|; frameNum = File.basename(fn).split("_").last.split(".json").first.to_i; FileUtils.cp(fn, outputFolder) if frameNum < maxFrames; end; true
