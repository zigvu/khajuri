import multiprocessing, time, os, logging
import math, sys, threading
import gc
import objgraph
import resource

class ThreadWorker(threading.Thread):
    def __init__(self, task, input_queue, output_queue):
        threading.Thread.__init__( self )
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.task = task

    def run(self):
        proc_name = self.name
        while True:
            next_object = self.input_queue.get()
            if next_object is None:
                # Poison pill means shutdown
                logging.info( '%s: Exiting' % self )
                self.input_queue.task_done()
                if self.output_queue:
                  self.output_queue.put(None)
                break
            logging.info( '%s processing : %s' % (self, next_object) )
            answer = self.task( next_object )
            self.input_queue.task_done()
            if self.output_queue:
              self.output_queue.put(answer)
        return

    def __str__( self ):
      return '( %s )' % self.task

class ProcessWorker(multiprocessing.Process):
    def __init__(self, task, input_queue, output_queue):
        multiprocessing.Process.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.task = task
        logging.info( 'Constructing Process %s with pid %s task as %s' % ( self.name, self.pid, self.task ) )

    def run(self):
        logging.info( 'Starting Process %s with pid %s task as %s' % ( self.name, self.pid, self.task ) )
        proc_name = self.name
        while True:
            next_object = self.input_queue.get()
            if next_object is None:
                # Poison pill means shutdown
                if self.output_queue:
                  self.output_queue.put(None)
                break
            logging.info( '%s processing : %s' % (self, next_object) )
            answer = self.task( next_object )
            self.input_queue.task_done()
            if self.output_queue:
              self.output_queue.put(answer)
            gc.collect()
            print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        logging.info( '%s: Exiting from Worker' % self )
        return

    def __str__( self ):
      return '( %s, %s )' % ( self.task, self.pid )

class Worker( ProcessWorker ):
  pass
