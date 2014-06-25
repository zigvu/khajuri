#!/usr/bin/python
import glob, sys
import os, tempfile, pdb
from multiprocessing import Process
import yaml, json

class OverSample( PostProcessor ):
  def __init__( self, config ):
    self.config = config

  def run( self ):
    raise NotImplementedError()
