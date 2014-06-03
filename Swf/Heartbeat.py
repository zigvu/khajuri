#!/usr/bin/env python
import time
class Heartbeat( object ):
  def __init__( self, worker ):
    self.lastheartBeat = time.time()
    self.worker = worker
    self.interval = 10

  def heartbeat( self ):
    if time.time() - self.lastheartBeat > self.interval:
       self.worker.heartbeat()
       self.lastheartBeat = time.time()
