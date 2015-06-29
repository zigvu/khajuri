#!/usr/bin/python
import sys, time, os, json, shutil
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager


description = \
"""
This script will recursively go into each folder of inputVideoFolder
and attempt to convert all video files that are (ffprob-able) into
the correct format and output in outputVideoFolder
"""

def convertFile(inputFileName, outputFolder):
  """Convert a video file into format expected by pipeline:
    - Change width/height to 720p specifications
    - Change frame rate to 25fps
    - Change container format to mp4
  """
  fps = 25
  finalScale = 'hd720'  # defined by ffmpeg constant
  requiredWidth = 1280
  requiredHeight = 720

  tempFile = '/tmp/ffprobeResults.json'
  shutil.rmtree(tempFile, ignore_errors=True)
  tempFileRedirect = ' > ' + tempFile + ' 2>&1'
  ffprobeCmd = 'ffprobe -v quiet -print_format json -show_streams '

  width = -1
  height = -1
  # see if video file
  ffprobe = ffprobeCmd + inputFileName + tempFileRedirect
  if os.system(ffprobe) == 0:
    with open(tempFile, 'r') as f:
      for line in f:
        if 'width' in line:
          width = int(line.split('"width": ')[1].split(',')[0])
        if 'height' in line:
          height = int(line.split('"height": ')[1].split(',')[0])
  else:
    print "Not video file: %s" % inputFileName
    return False

  # if have width and height
  if width == -1 or height == -1:
    print "Couldn't determine dimension of video: %s" % inputFileName
    return False

  # use ffmpeg to convert
  print "Processing video file: %s of dimension %d %d" % (
      inputFileName, width, height
  )

  try:
    os.makedirs(outputFolder)
  except OSError as exc:
    pass
  fileName, fileExtension = os.path.splitext(inputFileName)
  outputFileName = os.path.join(
      outputFolder, "%s.mp4" % os.path.basename(fileName))

  ffmpegCmd = 'ffmpeg -v quiet -i %s -r %d' % (inputFileName, fps)

  # compute new scale if required
  if width != requiredWidth or height != requiredHeight:
    widthRatio = 1.0 * requiredWidth / width
    heightRatio = 1.0 * requiredHeight / height
    if widthRatio > heightRatio:
      cropY = int((1.0 * height * widthRatio - requiredHeight) / 2)
      scaleFirst = 'scale=w=%d:h=-1,' % requiredWidth
      crop = 'crop=w=%d:h=%d:x=%d:y=0,' % (requiredWidth, requiredHeight, cropY)
      scaleSecond = 'scale=size=%s' % finalScale
      ffmpegCmd = '%s -vf " %s %s %s"' % (
          ffmpegCmd, scaleFirst, crop, scaleSecond
      )
    else:
      cropX = int((1.0 * width * heightRatio - requiredWidth) / 2)
      scaleFirst = 'scale=w=-1:h=%d,' % requiredHeight
      crop = 'crop=w=%d:h=%d:x=%d:y=0,' % (requiredWidth, requiredHeight, cropX)
      scaleSecond = 'scale=size=%s' % finalScale
      ffmpegCmd = '%s -vf " %s %s %s"' % (
          ffmpegCmd, scaleFirst, crop, scaleSecond
      )

  ffmpegCmd = '%s %s' % (ffmpegCmd, outputFileName)
  if os.system(ffmpegCmd) == 0:
    return True
  else:
    return False



def runVideoConversion(fileNameQueue, outputVideoFolder):
  """Process to convert video"""
  while True:
    fileName = fileNameQueue.get()
    if fileName is None:
      fileNameQueue.task_done()
      # poison pill means done with files
      break
    success = convertFile(fileName, outputVideoFolder)
    if success:
      print "Finished converting %s" % fileName
    fileNameQueue.task_done()

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print 'Usage %s <inputVideoFolder> <outputVideoFolder>' % sys.argv[0]
    print description

    sys.exit(1)
  inputVideoFolder = sys.argv[1]
  outputVideoFolder = sys.argv[2]

  fileNameQueue = JoinableQueue()

  for dirpath, dirs, files in os.walk(inputVideoFolder):
    for filename in files:
      inputFileName = os.path.join(dirpath, filename)
      fileNameQueue.put(inputFileName)

  # num of processes
  numOfProcesses = 8
  runVideoConversionProcesses = []
  for i in range(0,numOfProcesses):
    runVideoConversionProcess = Process(
        target=runVideoConversion, args=(fileNameQueue, outputVideoFolder, ))
    runVideoConversionProcesses += [runVideoConversionProcess]
    runVideoConversionProcess.start()
    fileNameQueue.put(None)

  for runVideoConversionProcess in runVideoConversionProcesses:
    runVideoConversionProcess.join()
  fileNameQueue.join()
