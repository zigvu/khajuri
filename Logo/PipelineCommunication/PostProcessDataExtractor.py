import sys, os, glob, subprocess
import multiprocessing
from multiprocessing import JoinableQueue, Queue, Process, Manager
from collections import OrderedDict
from fractions import Fraction
import logging, json

from Logo.PipelineCore.JSONReaderWriter import JSONReaderWriter
from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.VideoFrameReader import VideoFrameReader

def runLocalizationExtraction(caffeLabelIds, jsonFilesQueue, localizationResultsQueue):
  """Process to extract localizations from JSON files"""
  while True:
    jsonFileName = jsonFilesQueue.get()
    if jsonFileName is None:
      jsonFilesQueue.task_done()
      # poison pill means done with json reading
      break
    #logging.debug("Localization Extraction: Start extraction of file %s" % os.path.basename(jsonFileName))
    
    jsonReaderWriter = JSONReaderWriter(jsonFileName)
    frameNumber = jsonReaderWriter.getFrameNumber()
    # extract localizations
    extractedLocalizations = {}
    extractedLocalizations['frame_number'] = frameNumber
    extractedLocalizations['localizations'] = {}
    for caffeLabelId in caffeLabelIds:
      localizations = jsonReaderWriter.getLocalizations(caffeLabelId)
      extractedLocalizations['localizations'][caffeLabelId] = localizations

    # put in queue:
    localizationResultsQueue.put(extractedLocalizations)
    jsonFilesQueue.task_done()


class PostProcessDataExtractor( object ):
  """Class to extract data from caffe results to send to cellroti"""
  def __init__(self, configReader, videoId, videoFileName, \
    jsonFolder, outputFolder, detectableClassMapper):
    """Initialize values"""
    self.configReader = configReader
    self.videoId = videoId
    self.videoFileName = videoFileName
    self.jsonFolder = jsonFolder
    self.outputJSONFileName = os.path.join(outputFolder, "localizations.json")
    self.outputFramesFolder = os.path.join(outputFolder, "frames")
    ConfigReader.mkdir_p(self.outputFramesFolder)
    self.detectableClassMapper = detectableClassMapper

    self.ffprobeKeys = ['format', 'width', 'height', 'quality', \
      'length', 'playback_frame_rate', 'detection_frame_rate']

    self.detectionFrameRate = configReader.sw_frame_density
    self.numSecondsPerSampleFrame = configReader.ce_numSecondsPerSampleFrame
    self.num_consumers = max(int(self.configReader.multipleOfCPUCount * multiprocessing.cpu_count()), 1)

  def run(self):
    """Create the json file to send to cellroti"""
    ffprobeResults = self.run_ffprobe(self.videoFileName)
    relabeledLocalizations = self.extract_localizations(self.jsonFolder, self.detectableClassMapper)
    framesToExtract = self.get_frames_to_extract(relabeledLocalizations, self.detectableClassMapper)
    jsonToSave = {
      'video_id': self.videoId,
      'detections': relabeledLocalizations,
      'extracted_frames': framesToExtract,
      'video_attributes': ffprobeResults
    }
    self.save_state(self.outputJSONFileName, jsonToSave)
    self.extract_frames(framesToExtract, self.videoFileName, self.outputFramesFolder)

  def extract_localizations(self, jsonFolder, detectableClassMapper):
    """Extract localization for all classes in detectableClassMapper from json folder"""
    logging.info("Extracting all localizations")
    relabeledLocalizations = OrderedDict()
    caffeLabelIds = detectableClassMapper.get_mapped_caffe_label_ids()

    jsonFilesQueue = JoinableQueue()
    localizationResultsQueue = Queue()
    jsonFiles = glob.glob(os.path.join(jsonFolder, "*json")) + \
      glob.glob(os.path.join(jsonFolder, "*snappy"))

    for jsonFileName in jsonFiles:
      jsonFilesQueue.put(jsonFileName)

    # start reading JSON files in parallel
    localizationExtractors = []    
    for i in xrange(self.num_consumers):
      localizationExtractor = Process(\
        target=runLocalizationExtraction,\
        args=(caffeLabelIds, jsonFilesQueue, localizationResultsQueue))
      localizationExtractors += [localizationExtractor]
      localizationExtractor.start()
      # for each process, put a poison pill in queue
      jsonFilesQueue.put(None)

    logging.debug("Localization Extraction: Started all processes for localization extraction")

    # wait for all extraction processes to complete
    jsonFilesQueue.join()

    # collate all results:
    logging.debug("Localization Extraction: Mapping localizations to cellroti IDs")
    while localizationResultsQueue.qsize() > 0:
      extractedLocalizations = localizationResultsQueue.get()
      frameNumber = extractedLocalizations['frame_number']
      relabeledLocalizations[frameNumber] = {}
      for caffeLabelId in caffeLabelIds:
        localizations = extractedLocalizations['localizations'][caffeLabelId]
        if len(localizations) > 0:
          cellrotiDetectableId = detectableClassMapper.get_detectable_database_id(caffeLabelId)
          relabeledLocalizations[frameNumber][cellrotiDetectableId] = localizations

    logging.debug("Localization Extraction: Waiting for threads to join")
    for localizationExtractor in localizationExtractors:
      localizationExtractor.join()

    # sort based on frame numbers
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

  def get_frames_to_extract(self, relabeledLocalizations, detectableClassMapper):
    """For each class, get the frame number with the highest score across a window of frames"""
    logging.info("Determining frames to extract")
    numFrameIntervalPerFrameSaved = self.numSecondsPerSampleFrame * self.detectionFrameRate
    cellrotiDetectableIds = detectableClassMapper.get_detectable_database_ids()
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
    
          # get frame rate and convert to float
          fps = 0
          if "r_frame_rate" in streamJSON:
            fps = streamJSON["r_frame_rate"]
          elif "avg_frame_rates" in streamJSON:
            fps = streamJSON["avg_frame_rates"]
          try:
            fps = Fraction(fps) + 0.0
          except:
            raise RuntimeError("Frame rate for video %s couldn't be found" % videoFileName)
          ffprobeResults['playback_frame_rate'] = fps

      # get length
      start_time = float(ffprobeJSON["format"]["start_time"])
      duration = float(ffprobeJSON["format"]["duration"])
      length = int((duration - start_time) * 1000) # get length in milliseconds
      ffprobeResults['length'] = length

    except:
      logging.error("Command: '%s'" % ffprobeCmd)
      logging.error("Could not run ffprobe in video file %s" % videoFileName)

    ffprobeResults['detection_frame_rate'] = self.detectionFrameRate

    # error check
    for k in self.ffprobeKeys:
      if not k in ffprobeResults:
        raise RuntimeError("FFprobe couldn't find %s in video" % k)
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

