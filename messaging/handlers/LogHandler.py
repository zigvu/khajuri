import json
import graypy

from messaging.infra.Pickler import Pickler
from messaging.type.Headers import Headers


class LogHandler(object):
  """Handle sending log data to GrayLog2"""

  def __init__(self, config):
    """Initialize values"""
    self.config = config
    self.logger = self.config.logging.logger
    self.handler = graypy.GELFHandler('localhost', 12201)

  def handle(self, headers, message):
    self.handler.handle(message)
    self.logger.debug("Saving log")

    # TODO: error check
    responseHeaders = Headers.statusSuccess()
    responseMessage = {}
    return responseHeaders, json.dumps(responseMessage)

  # input to this function is a pickled object, output is JSON
  def __call__(self, headers, message):
    return self.handle(headers, Pickler.unpickle(message))
