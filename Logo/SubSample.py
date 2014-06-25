#!/usr/bin/python
import glob, sys
import os, tempfile, pdb
from multiprocessing import Process
import yaml, json

class SubSample( PostProcessor ):
  def __init__( self, config ):
    self.config = config
    self.patchesToSample = []

  def savePatchForSubSample( self, frameId, patchId ):
    self.patchesToSample.append( ( frameId, patchId ) )

  def run( self ):
    raise NotImplementedError()
