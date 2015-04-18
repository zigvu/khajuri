import multiprocessing, time, os, logging
import math, sys
from Worker import Worker

class Pipeline( object ):
  def __init__( self, tasks, inputQueue, output ):
    self.tasks = tasks
    self.inputQueue = inputQueue
    self.output = output
    self.numOfWorkers = multiprocessing.cpu_count()
    self.workers = {}
    self.inputQueues = []
    self.setup()

  def setup( self ):
    inputQueue = self.inputQueue
    interMediateQueue = multiprocessing.JoinableQueue()
    for task in self.tasks:
      self.inputQueues.append( inputQueue )
      self.workers[ task ] =\
           [ Worker( task, inputQueue, interMediateQueue ) for i in xrange( self.numOfWorkers ) ]
      inputQueue = interMediateQueue
      interMediateQueue = multiprocessing.JoinableQueue()

    for w in self.workers[ task ]:
       w.output_queue = self.output

  def start( self ):
    for task in self.tasks:
       for w in self.workers[ task ]:
         w.start()

  def join( self ):
    for inputQueue in self.inputQueues:
      inputQueue.join()
