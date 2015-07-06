#!/usr/bin/python

import os, logging, subprocess, sys

baseScriptDir = os.path.dirname(os.path.realpath(__file__))


class Version(object):

  def runCmd(self, cmd, cwd):
    args = cmd.split()
    output = subprocess.check_output(
        args, stderr=subprocess.STDOUT, cwd=cwd)
    return output

  def logVersion(self):
    gitShow = self.runCmd("git show", baseScriptDir)
    commit = None
    for line in gitShow.split('\n'):
      if line.startswith('commit'):
        commit = line
    gitBranch = self.runCmd("git branch", baseScriptDir)
    branch = None
    for line in gitBranch.split('\n'):
      if line.startswith('*'):
        branch = line
    logging.info('Branch: %s' % branch)
    logging.info(commit)


if __name__ == '__main__':
  logging.basicConfig(
      format='{%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
      level=logging.INFO)
  v = Version()
  v.logVersion()
