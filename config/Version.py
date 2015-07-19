#!/usr/bin/python

import os
import subprocess
import sys

baseScriptDir = os.path.dirname(os.path.realpath(__file__))


class Version(object):

  def runCmd(self, cmd, cwd):
    args = cmd.split()
    output = subprocess.check_output(args, stderr=subprocess.STDOUT, cwd=cwd)
    return output

  def getGitVersion(self):
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
    return branch, commit


if __name__ == '__main__':
  v = Version()
  branch, commit = v.getGitVersion()
  print "Branch: %s" % branch
  print "Commit: %s" % commit
