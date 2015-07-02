#!/usr/bin/python

import sys, os, glob, logging, time
from multiprocessing import JoinableQueue, Process, Manager
import pika
import graypy

from config.Config import Config
from config.ZLogging import ZLoggingQueueProducer, ZLogging, ZLoggingStreamHandler

from Logo.PipelineCore.LogConsolidator import LogConsolidator

from messaging.infra.RpcClient import RpcClient

def generateLogs(config):
  logger = config.logger
  for i in range(0,10):
    logger.info("Run ID: %d" % i)
    time.sleep(1)

def sendLogToRabbit(config):
  logConsolidator = LogConsolidator(config)
  # finally start log consolidation
  logConsolidator.startConsolidation()

def main():
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    sys.exit(1)

  configFileName = sys.argv[1]
  config = Config(configFileName)
  logger = config.logger

  rabbitSendLogProcess = Process(target=sendLogToRabbit, args=(config, ))
  rabbitSendLogProcess.start()
  # printLogProcess = Process(target=printLogs, args=(config, ))
  # printLogProcess.start()

  generateLogProcess1 = Process(target=generateLogs, args=(config, ))
  generateLogProcess1.start()

  # generateLogProcess2 = Process(target=generateLogs, args=(config, ))
  # generateLogProcess2.start()

  generateLogProcess1.join()
  # generateLogProcess2.join()

  config.logQueue.put(None)
  # printLogProcess.join()
  rabbitSendLogProcess.join()
  config.logQueue.join()
  # logger = ZLogging(logging.DEBUG, {}).getLogger()
  # logger.info("Whaa")






def printLogs(config):
  zLoggingStreamHandler = ZLoggingStreamHandler()
  while True:
    logMsg = config.logQueue.get()
    # all logs are generated
    if logMsg is None:
      config.logQueue.task_done()
      # poison pill means done with logging
      break
    # generated logs
    zLoggingStreamHandler.handle(logMsg)
    # print "%s" % logMsg
    config.logQueue.task_done()


def printLogs_gelf(config):
  # my_logger = logging.getLogger('test_logger')
  # my_logger.setLevel(logging.DEBUG)

  # handler = graypy.GELFRabbitHandler('amqp://guest:guest@localhost/%2F', 'logging.gelf')
  handler = graypy.GELFHandler('localhost', 12201)
  # my_logger.addHandler(handler)

  # my_logger.debug('Hello Graylog2.')
  while True:
    logMsg = config.logQueue.get()
    # all logs are generated
    if logMsg is None:
      config.logQueue.task_done()
      # poison pill means done with logging
      break
    # generated logs
    handler.handle(logMsg)
    # print "%s" % logMsg
    config.logQueue.task_done()


def printLogs_rabbig(config):
  amqp_url = 'localhost'
  exchange = 'zigvu.log'
  serverQueueName = 'vm2.kahjuri.development.log'
  connection = pika.BlockingConnection(pika.ConnectionParameters(
      host=amqp_url,
      heartbeat_interval=(60 * 10)))
  channel = connection.channel()
  channel.exchange_declare(exchange=exchange, type='fanout', durable=True)
  channel.queue_bind(exchange=exchange, queue=serverQueueName)
  properties = pika.BasicProperties(delivery_mode=2)

  while True:
    logMsg = config.logQueue.get()
    # all logs are generated
    if logMsg is None:
      config.logQueue.task_done()
      # poison pill means done with logging
      break
    # generated logs
    message = logMsg
    print "%s" % logMsg
    channel.basic_publish(
        exchange=exchange,
        routing_key=serverQueueName,
        properties=properties,
        body=message)
    config.logQueue.task_done()

  # done - close connection
  connection.close()

def main_old():
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

  # generateLogProcess2 = Process(target=generateLogs, args=(config, ))
  # generateLogProcess2.start()

  generateLogProcess1.join()
  # generateLogProcess2.join()

  config.logQueue.put(None)
  printLogProcess.join()
  config.logQueue.join()
  # logger = ZLogging(logging.DEBUG, {}).getLogger()
  # logger.info("Whaa")


def main_two():
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    sys.exit(1)

  print "Loading config..."
  configFileName = sys.argv[1]
  e = Config(configFileName)

  print "VideoId: %s" % e.job.videoId
  print "Env: %s" % e.environment
  print "Mchn GPUs: %s" % e.machine.useGPU()
  print "JobId: %s" % e.job.zigvuJobId
  print "Storage hdf5: %s" % e.storage.enableHdf5ReadWrite
  print "CPP Logger: %s" % e.logging.cppGlogStarted
  print "SW scales: %s" % e.slidingWindow.sw_scales
  print "SW bbx len: %s" % e.slidingWindow.numOfSlidingWindows
  # print "Mes videoData: %s" % e.messaging.queues.videoData
  print "Done loading config..."

  logger = ZLogging(logging.DEBUG, {'zigvuJobId': 1, 'environment': 'local'}).getLogger()
  logger.info("Whaa")

if __name__ == '__main__':
  main_two()
