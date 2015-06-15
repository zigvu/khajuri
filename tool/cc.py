#!/usr/bin/python

import sys, os, glob, logging

from postprocessing.task.CompareFrame import CompareFrame
from postprocessing.task.OldJsonReader import OldJsonReader
from postprocessing.task.JsonReader import JsonReader
from config.Config import Config
from config.Status import Status
from config.Version import Version

def main():
  if len(sys.argv) < 6:
    print 'Usage %s <config.yaml> <file1> <old/new> <file2> <old/new>' % sys.argv[ 0 ]
    print 'This executable will compare two files and print any diff per class'
    sys.exit(1)
  logging.basicConfig(
    format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
    level=logging.INFO, datefmt="%Y-%m-%d--%H:%M:%S"
    )
  config = Config( sys.argv[ 1 ] )
  config.videoId = None
  Version().logVersion()
  status = Status()
  frame1 = None
  frame2 = None

  f1 = sys.argv[2]
  f1Format = sys.argv[ 3 ]
  f2 = sys.argv[4]
  f2Format = sys.argv[ 5 ]

  if f1Format == 'old':
    frame1, classIds = OldJsonReader( config, status ) ( f1 )
  else:
    frame1, classIds = JsonReader( config, status ) ( f1 )

  if f2Format == 'old':
    frame2, classIds = OldJsonReader( config, status ) ( f2 )
  else:
    frame2, classIds = JsonReader( config, status ) ( f2 )

  compare = CompareFrame( config, status )
  diff = compare( ( frame1, frame2 ) )
  if diff:
    print 'Diff is %s' % diff
  else:
    print 'Same Frame'

if __name__ == '__main__':
  main()
