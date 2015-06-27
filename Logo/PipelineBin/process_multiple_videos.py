#!/usr/bin/python

import sys, os, glob
import time
from subprocess import call

# baseScriptDir = os.path.dirname(os.path.realpath(__file__))
# sys.path.append('%s/../../VideoReader' % baseScriptDir)

# from Logo.PipelineThread.VideoProcessThread import VideoProcessThread

description = \
"""
This script will run all videos found in the configs folder
"""

def main():
  if len(sys.argv) < 2:
    print 'Usage %s <configs_folder>' % sys.argv[0]
    print description
    sys.exit(1)

  configsFolder = sys.argv[1]

  # iterate over all files:
  for dirpath, dirs, files in os.walk(configsFolder):
    for filename in files:
      configFileName = os.path.join(dirpath, filename)
      print "Working on file: %s"% configFileName
      try:
        call(["~/khajuri/Logo/PipelineBin/process_video", configFileName])
      except Exception, e:
        print "Couldn't run file: %s"% configFileName
        time.sleep(10)
        call(["pkill", "processvideo"])
        time.sleep(10)
      finally:
        pass

if __name__ == '__main__':
  main()
