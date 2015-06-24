#!/usr/bin/python

import sys, os, glob, logging, time
from multiprocessing import JoinableQueue, Process, Manager


from config.Config import Config
from config.ZLogging import ZLoggingQueueProducer, ZFormatter

def generateLogs(config):
  logger = config.logger
  for i in range(0,10):
    logger.info("Run ID: %d" % i)
    time.sleep(1)

def printLogs(config):
  while True:
    logMsg = config.logQueue.get()
    # all logs are generated
    if logMsg is None:
      config.logQueue.task_done()
      # poison pill means done with logging
      break
    # generated logs
    print "%s" % logMsg
    config.logQueue.task_done()

def main():
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    sys.exit(1)

  configFileName = sys.argv[1]
  config = Config(configFileName)
  two = 2
  logger = config.logger
  logger.info('Loaded logging infrastructure %d' % two + " ha.")

  printLogProcess = Process(target=printLogs, args=(config, ))
  printLogProcess.start()

  generateLogProcess1 = Process(target=generateLogs, args=(config, ))
  generateLogProcess1.start()

  generateLogProcess2 = Process(target=generateLogs, args=(config, ))
  generateLogProcess2.start()

  generateLogProcess1.join()
  generateLogProcess2.join()

  config.logQueue.put(None)
  printLogProcess.join()
  config.logQueue.join()


if __name__ == '__main__':
  main()
