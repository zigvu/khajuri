#!/usr/bin/env python
import csv, glob, logging, sys, os
import matplotlib.pyplot as plt
import numpy as np
import json


if __name__ == '__main__':
  if len( sys.argv ) < 6:
    print 'Usage %s <csv_folder> <score_threshold> <count_threshold> <class_mapping> <output_folder>' % sys.argv[ 0 ]
    sys.exit( 1 )
  
  csvFolder = sys.argv[ 1 ]
  scoreThreshold = float( sys.argv[ 2 ] )
  countThreshold = float( sys.argv[ 3 ] )
  classMappingFile = sys.argv[ 4 ]
  outputFolder = sys.argv[ 5 ]
  
  logging.basicConfig(
      format='{%(filename)s:%(lineno)d} %(levelname)s PID:%(process)d - %(message)s',
      level=logging.INFO )
  
  logging.info( 'Using folder %s' % csvFolder )
  logging.info( 'Using score threshold %s' % scoreThreshold )
  logging.info( 'Using count threshold %s' % countThreshold )
  
  scores = {}
  imgByClass = {}
  classMapping = json.load( open( classMappingFile, 'r' ) )
  
  for f in glob.glob( os.path.join( csvFolder, '*.csv' ) ):
    logging.info( 'Reading file %s' % f )
    with open(f, 'rb') as myFile:
      className = os.path.splitext( os.path.basename( f ) ) [ 0 ]
      reader = csv.reader( myFile )
      header = False
      for row in reader:
        if not header:
          header = True
          continue
        else:
          # logging.info( '%s' % row )
          imgByClass[ row[0] ] = className
          if len( row ) > 0:
            for i in range( 1, len( row ) ):
              scores [ ( row[0], classMapping[ "%s" % ( i - 1 ) ] ) ] = float( row[ i ] )
          else:
            break

  # Filter Using the scoreThreshold
  filteredScores = {}
  for k, v in scores.iteritems():
    if v >= scoreThreshold:
      filteredScores[ k ] = v

  countHeatMap = {}
  avgScoreHeatMap = {}
  patchListToExamine = {} 
  for clsA in classMapping.values():
    for clsB in classMapping.values():
      countHeatMap[ ( clsA, clsB ) ] = 0
      avgScoreHeatMap[ ( clsA, clsB ) ] = 0
      if clsA != clsB:
        patchListToExamine[ ( clsA, clsB ) ] = []
  
  for k, v in filteredScores.iteritems():
    clsA = imgByClass[ k[ 0 ] ]
    clsB = k[ 1 ]
    countHeatMap[ ( clsA, clsB ) ] += 1
    avgScoreHeatMap[ ( clsA, clsB ) ] += v
    avgScoreHeatMap[ ( clsA, clsB ) ] /= 2
    if v >= scoreThreshold and clsA != clsB :
      patchListToExamine[ ( clsA, clsB ) ].append( { 'patch': k[0], 'score' : v } )

  patchListToExamineForJson = {}
  for k, v in patchListToExamine.iteritems():
    if not v:
      continue
    patchListToExamineForJson[ "(%s,%s)" % k ] = v
  patchDumpJsonFile = os.path.join( outputFolder, "patches.json" )
  json.dump( patchListToExamineForJson,  open( patchDumpJsonFile, 'w' ), indent=2 )
  
  print 'Confusion Matrix:'
  print 'Confusion Counts greater than %s:' % countThreshold
  for k, v in countHeatMap.iteritems():
    if k [ 0 ] == k[ 1]:
      continue
    if v >= countThreshold:
      print '%50s:->%s' % ( k, v )
  
  print 'ConfusionAvg Scores greater than %s:' % scoreThreshold
  for k, v in avgScoreHeatMap.iteritems():
    if k [ 0 ] == k[ 1]:
      continue
    if v >= scoreThreshold:
      print '%50s:->%s' % ( k, v )
   
  # CSV Output
  #  writer = csv.writer(open(os.path.join( outputFolder, 'confusion_count.csv' ), 'wb'))
  #  for key, value in countHeatMap.items():
  #    writer.writerow([key, value])
  #  writer = csv.writer(open( os.path.join( outputFolder, 'confusion_avgScore.csv' ), 'wb'))
  #  for key, value in avgScoreHeatMap.items():
  #  writer.writerow([key, value])
