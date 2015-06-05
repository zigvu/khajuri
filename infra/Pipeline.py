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

    interMediateQueue.join()
    for w in self.workers[ task ]:
       w.output_queue = self.output

  def start( self ):
    for task in self.tasks:
       for w in self.workers[ task ]:
         w.start()

  def join( self ):
    logging.info( 'Joining all inputQueues' )
    for inputQueue in self.inputQueues:
      inputQueue.join()
    logging.info( 'Done with Joining all inputQueues' )
    logging.info( 'Joining all outputQueues' )
    while not self.output.empty():
      logging.info( 'Results in not empty - extracing item' )
      logging.info( 'Result %s' % str( self.output.get_nowait() ) )
    logging.info( 'Done with Joining all outputQueues' )
    logging.info( 'Joining all workers' )
    for t, workers in self.workers.items():
      logging.info( 'Joining for task %s' % t )
      for w in workers:
        logging.info( 'Joining %s' % w )
        if not w.task_done:
          logging.info( 'Not Done = State is alive %s, exitcode: %s' % ( w.is_alive, w.exitcode ) )
        w.terminate()
        logging.info( 'Joined' )
