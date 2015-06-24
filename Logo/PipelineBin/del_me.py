#!/usr/bin/python

import sys, os, glob, logging, time
from multiprocessing import JoinableQueue, Process, Manager


from config.Config import Config
from config.ZLogging import ZLoggingQueueProducer

def generateLogs(logQueue):
  logLevel = logging.DEBUG
  formatMsg = {
    'kheer_job_id': 1
  }
  logger = ZLoggingQueueProducer(logQueue, logLevel, formatMsg).getLogger()
  for i in range(0,10):
    logger.info("Run ID: %d" % i)
    time.sleep(1)

def printLogs(logQueue):
  while True:
    logMsg = logQueue.get()
    # all logs are generated
    if logMsg is None:
      logQueue.task_done()
      # poison pill means done with logging
      break
    # generated logs
    print "%s" % logMsg
    logQueue.task_done()

def main():
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    sys.exit(1)

  # logQueue = JoinableQueue()
  # printLogProcess = Process(target=printLogs, args=(logQueue, ))
  # printLogProcess.start()

  # generateLogProcess1 = Process(target=generateLogs, args=(logQueue, ))
  # generateLogProcess1.start()

  # generateLogProcess2 = Process(target=generateLogs, args=(logQueue, ))
  # generateLogProcess2.start()

  # logQueue.put(None)

  # printLogProcess.join()
  # generateLogProcess1.join()
  # generateLogProcess2.join()
  # logQueue.join()

  configFileName = sys.argv[1]
  config = Config(configFileName)
  two = 2
  logger = config.logger
  logger.info('Loaded logging infrastructure %d' % two + " ha.")


if __name__ == '__main__':
  main()
