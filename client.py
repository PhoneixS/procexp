"""linux process explorer client"""

import utils
import communication.tcp
import time 

class ProcExpClient(object):
  """reads from a linux process explorer server and can send data to the server"""
  def __init__(self, dataCallback, address):
    self.__address__ = address
    self.__stop__ = False
    self.__cb__ = dataCallback
    self.__client__ = None
    
  def stop(self):
    """stop the client"""
    self.__stop__ = True
    self.__client__.close()
    for t in self.getData.running:
      t.join()
      
  @utils.asynchronous(None)
  def getData(self):
    """get data from a procexp server"""
    while self.__stop__ == False:
      while self.__stop__ == False and self.__client__ == None:
        try:
          self.__client__ = communication.tcp.Client(self.__address__)
        except communication.tcp.TCPError:
          time.sleep(0.1)
      while self.__stop__ == False:
        try:
          newReader = self.__client__.receive()
          self.__cb__(newReader)
        except:
          client = None
          break