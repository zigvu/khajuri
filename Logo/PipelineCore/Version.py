#!/usr/bin/python

import os, logging, subprocess

class LogoVersion( object ):
  def runCmd( self, cmd ):
    args = cmd.split()
    output = subprocess.check_output(
        args, stderr=subprocess.STDOUT )
    return output

  def logVersion( self ):
    gitShow = self.runCmd( "git show" )
    commit = None
    for line in gitShow.split('\n'):
      if line.startswith( 'commit' ):
        commit = line
    gitBranch = self.runCmd( "git branch" )
    branch = None
    for line in gitBranch.split('\n'):
      if line.startswith( '*' ):
        branch = line
    logging.debug( 'Branch: %s' % branch )
    logging.debug( commit )

if __name__ == '__main__':
  logging.basicConfig(format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s', level=logging.DEBUG)
  v = LogoVersion()
  v.logVersion()
