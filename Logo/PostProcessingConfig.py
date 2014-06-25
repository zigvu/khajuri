#!/usr/bin/python
import glob, sys
import os, tempfile, pdb
from multiprocessing import Process
import yaml, json

class PostProcessConfig( object ):
  def __init__( self, configFile, intputDir, outputDir ):
    self.yamlConfig = yaml.load( open( configFile, 'r' ) )
    self.intputDir = intputDir
    self.outputDir = outputDir

  def getModes( self ):
    return self.yamlConfig['mode'].split()

  def getDirToSavePredictions( self ):
    return self.yamlConfig['resultFolder']['Predictor']

  def getDirToSaveSubSample( self ):
    return self.yamlConfig['resultFolder']['SubSample']

  def getDirToSaveOverSample( self ):
    return self.yamlConfig['resultFolder']['OverSample']

  def getDirToSaveHeatMapDump( self ):
    return self.yamlConfig['resultFolder']['HeatMapDump']

  def getInputDir( self ):
    return self.intputDir

  def getOutputir( self ):
    return self.outputDir
