#!/usr/bin/env python

from AnnotatedFrame import FrameDumpReader
from RandomRectGenerator import MAXANNOTATIONPERFRAME
import sys

def printFrame( f ):
  print 'This frame has %s annotations' % len( f.annotations )
  for r in f.annotations:
    print r
  print f.frame

def read( fileName ):
  fdr = FrameDumpReader( fileName, MAXANNOTATIONPERFRAME )
  total = 0
  for f in fdr:
    total += 1
    printFrame( f )
  print 'Total frames %s' % total

if __name__ == '__main__':
  read( sys.argv[ 1 ] )
