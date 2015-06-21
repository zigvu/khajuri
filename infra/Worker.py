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
            gc.collect()
            print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return

    def __str__( self ):
      return '( %s )' % self.task

class Worker( ProcessWorker ):
  pass
