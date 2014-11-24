import sys, os, glob, subprocess
from collections import OrderedDict
from fractions import Fraction
import logging, json

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.VideoFrameReader import VideoFrameReader

class PostProcessDataExtractor( object ):
  """Class to extract data from caffe results to send to cellroti"""
  def __init__(self, videoId, videoFileName, jsonFolder, outputFolder, cellrotiDetectables):
    """Initialize values"""
    self.videoId = videoId
    self.videoFileName = videoFileName
    self.jsonFolder = jsonFolder
    self.outputJSONFileName = os.path.join(outputFolder, "localizations.json")
    self.outputFramesFolder = os.path.join(outputFolder, "frames")
    ConfigReader.mkdir_p(self.outputFramesFolder)
    self.cellrotiDetectables = cellrotiDetectables

    # TODO: get from config
    self.detectionFrameRate = 5
    self.numSecondsForSingleFrameSaved = 2

  def run(self):
    """Create the json file to send to cellroti"""
    relabeledLocalizations = self.extract_localizations(self.jsonFolder, self.cellrotiDetectables)
    framesToExtract = self.get_frames_to_extract(relabeledLocalizations, self.cellrotiDetectables)
    self.extract_frames(framesToExtract, self.videoFileName, self.outputFramesFolder)
    ffprobeResults = self.run_ffprobe(self.videoFileName)
    jsonToSave = {
      'video_id': self.videoId,
      'detections': relabeledLocalizations,
      'extracted_frames': framesToExtract,
      'video_attributes': ffprobeResults
    }
    self.save_state(self.outputJSONFileName, jsonToSave)

  def extract_localizations(self, jsonFolder, cellrotiDetectables):
    """Extract localization for all classes in cellrotiDetectables from json folder"""
    logging.info("Extracting all localizations")
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

  def extract_frames(self, framesToExtract, videoFileName, outputFramesFolder):
    """Given an array of frames, dump all frames to outputFramesFolder"""
    logging.info("Extracting frames from video")
    # get all unique frames in sorted order
    allFrameNumbers = []
    for cls in framesToExtract:
      allFrameNumbers += framesToExtract[cls]
    allFrameNumbers = list(set(allFrameNumbers))
    allFrameNumbers.sort()
    # extract frames
    videoFrameReader = VideoFrameReader(videoFileName)
    for currentFrameNum in allFrameNumbers:
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))
      if frame == None:
        break
      else:
        logging.debug("Extracting frame number %d" % currentFrameNum)
        imageFileName = os.path.join(outputFramesFolder, "%d.png" % currentFrameNum)
        videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), str(imageFileName))
    # done extracting frame - close gracefully
    logging.debug("Done with frame extraction - waiting for videoFrameReader to close")
    videoFrameReader.close()
    return True

  def get_frames_to_extract(self, relabeledLocalizations, cellrotiDetectables):
    """For each class, get the frame number with the highest score across a window of frames"""
    logging.info("Determining frames to extract")
    numFrameIntervalPerFrameSaved = self.numSecondsForSingleFrameSaved * self.detectionFrameRate
    cellrotiDetectableIds = cellrotiDetectables.get_detectable_database_ids()
    frameTrackers = OrderedDict()
    framesToStore = OrderedDict()
    # init container
    for cellrotiDetectableId in cellrotiDetectableIds:
      frameTrackers[cellrotiDetectableId] = {
        'counter': 0,
        'maxScore': -1.0,
        'maxScoreFrameNum': -1
      }
      framesToStore[cellrotiDetectableId] = []
    # loop through all frame localizations and find max frames
    for frameNum in relabeledLocalizations:
      for cellrotiDetectableId in cellrotiDetectableIds:
        if frameTrackers[cellrotiDetectableId]['counter'] < numFrameIntervalPerFrameSaved:
          # see if score peaked
          try:
            for patch in relabeledLocalizations[frameNum][cellrotiDetectableId]:
              if frameTrackers[cellrotiDetectableId]['maxScore'] < patch['score']:
                frameTrackers[cellrotiDetectableId]['maxScore'] = patch['score']
                frameTrackers[cellrotiDetectableId]['maxScoreFrameNum'] = frameNum
          except:
            # do nothing if there is no score for this class
            pass
        else:
          # store last cycle results
          if frameTrackers[cellrotiDetectableId]['maxScoreFrameNum'] != -1:
            framesToStore[cellrotiDetectableId] += [frameTrackers[cellrotiDetectableId]['maxScoreFrameNum']]
          # reset counters
          frameTrackers[cellrotiDetectableId]['counter'] = 0
          frameTrackers[cellrotiDetectableId]['maxScore'] = -1.0
          frameTrackers[cellrotiDetectableId]['maxScoreFrameNum'] = -1

        # increase counters
        frameTrackers[cellrotiDetectableId]['counter'] += 1
        # end if
    # return final frames to capture      
    return framesToStore

  def run_ffprobe(self, videoFileName):
    """Run ffprobe and save video related information in JSON"""
    logging.info("Running ffprobe on video file")
    ffprobeCmd = "ffprobe -v quiet -print_format json -show_format -show_streams %s" % videoFileName

    ffprobeResults = OrderedDict()
    try:
      ffprobeResult = subprocess.Popen(ffprobeCmd, shell=True, stdout=subprocess.PIPE).stdout.read()
      ffprobeJSON = json.loads(ffprobeResult)
      for streamJSON in ffprobeJSON['streams']:
        if streamJSON["codec_type"] == "video":
          format = streamJSON["codec_name"]
          ffprobeResults['format'] = format
          
          width = int(streamJSON["width"])
          height = int(streamJSON["height"])
          quality = self.get_video_quality(width, height)

          ffprobeResults['width'] = width
          ffprobeResults['height'] = height
          ffprobeResults['quality'] = quality

          start_time = float(streamJSON["start_time"])
          duration = float(streamJSON["duration"])
          length = (duration - start_time) * 1000
          ffprobeResults['length'] = length

          # get frame rate and convert to float
          fps = 0
          if "r_frame_rate" in streamJSON:
            fps = streamJSON["r_frame_rate"]
          elif "avg_frame_rates" in streamJSON:
            fps = streamJSON["avg_frame_rates"]
          try:
            fps = Fraction(fps) + 0.0
          except:
            fps = 0.0
            logging.error("Frame rate for video %s couldn't be found" % videoFileName)
          ffprobeResults['playback_frame_rate'] = fps
    except:
      logging.error("Command: '%s'" % ffprobeCmd)
      logging.error("Could not run ffprobe in video file %s" % videoFileName)

    ffprobeResults['detection_frame_rate'] = self.detectionFrameRate
    return ffprobeResults

  def get_video_quality(self, width, height):
    """Get video quality from the width and height"""
    if width >=720 or height >= 720:
      return "High"
    elif width >=480 or height >= 480:
      return "Medium"
    else:
      return "Low"

  def save_state(self, outputJSONFileName, outputDict):
    """Save json to file"""
    logging.info("Saving JSON to file")
    with open(outputJSONFileName, "w") as f :
      json.dump(outputDict, f, indent=2 )

# ruby file copy:
# require 'fileutils'
# inputFolder = '/home/evan/WinMLVision/Videos/Logo/WorldCup/wc14-BraNed-HLTS/json-all'; outputFolder = '/home/evan/Vision/temp/sendto_cellroti/json'
# maxFrames = 500; Dir["#{inputFolder}/*"].each do |fn|; frameNum = File.basename(fn).split("_").last.split(".json").first.to_i; FileUtils.cp(fn, outputFolder) if frameNum < maxFrames; end; true
