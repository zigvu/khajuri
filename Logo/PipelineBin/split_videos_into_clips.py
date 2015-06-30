#!/usr/bin/python

import sys, os, glob
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append('%s/../../VideoReader' % baseScriptDir)

from Logo.PipelineThread.VideoSplitterThread import VideoSplitterThread

description = \
"""
This script will recursively go into each folder of inputVideoFolder
and convert each video file into clips for use with kheer.
It will also embed any required frame number tracking pixels.
"""

def runClipCreation(fileNameQueue, configFileName, clipsOutputFolder):
  """Split video into clips"""
  while True:
    fileName = fileNameQueue.get()
    if fileName is None:
      fileNameQueue.task_done()
      # poison pill means done with files
      break
    # save in same folder as clip name
    clipBaseName = os.path.basename(fileName).split('.')[0]
    clipFolder = os.path.join(clipsOutputFolder, clipBaseName)
    videoSplitterThread = VideoSplitterThread(
        configFileName, fileName, clipFolder)
    videoSplitterThread.run()
    fileNameQueue.task_done()


def main():
  if len(sys.argv) < 4:
    print 'Usage %s ' % sys.argv[0] + \
        '<config.yaml> <inputVideoFolder> <clipsOutputFolder>'
    print description
    sys.exit(1)

  configFileName = sys.argv[1]
  inputVideoFolder = sys.argv[2]
  clipsOutputFolder = sys.argv[3]

  fileNameQueue = JoinableQueue()

  for dirpath, dirs, files in os.walk(inputVideoFolder):
    for filename in files:
      inputFileName = os.path.join(dirpath, filename)
      fileNameQueue.put(inputFileName)

  # num of processes
  numOfProcesses = 4
  runVideoSplitProcesses = []
  for i in range(0,numOfProcesses):
    runVideoSplitProcess = Process(
        target=runClipCreation, 
        args=(fileNameQueue, configFileName, clipsOutputFolder, ))
    runVideoSplitProcesses += [runVideoSplitProcess]
    runVideoSplitProcess.start()
    fileNameQueue.put(None)

  for runVideoSplitProcess in runVideoSplitProcesses:
    runVideoSplitProcess.join()
  fileNameQueue.join()



if __name__ == '__main__':
  main()
