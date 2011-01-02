"""linux process explorer client"""

import utils
import communication.tcp
import time 
import threading

class ProcExpClient(object):
  """reads from a linux process explorer server and can send data to the server"""
  def __init__(self, dataCallback, address):
    self.__address__ = address
    self.__stop__ = False
    self.__cb__ = dataCallback
    self.__client__ = None
    self.__sendLock__ = threading.Lock()
    
  def stop(self):
    """stop the client"""
    self.__stop__ = True
    self.__client__.close()
    for t in self.getData.running:
      t.join()
      
  def sendData(self, data):
    """send data to server"""
    with self.__sendLock__:
      self.__client__.send(data)
      
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
        except communication.tcp.TCPError:
          self.__client__ = None
          break
        except:
          import traceback
          print traceback.format_exc()