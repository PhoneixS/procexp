"""tcp server for procexp graphical clients"""
import utils
import threading
import communication.tcp




class procexpServer(object):
  """process explorer /proc server"""
  def __init__(self, address):
    self.__clients_lock__ = threading.Lock()
    self.__address__ = address
    self.__server__ = None
    self.__clients__ = []
    self.__stop__ = False
    
  def sendData(self, data):
    """send data to all clients"""
    with self.__clients_lock__:
      for client in self.__clients__:
        try:
          client.send(data)        
        except:
          self.__clients__.remove(client)

  def stopServer(self):
    """stop the server"""
    self.__stop__ = True
    self.__server__.close()
    for t in self.doServe.running:
      t.join()
  
  @utils.asynchronous(None)
  def doServe(self):
    '''Accepts clients and adds them to list'''
    try:
      self.__server__ = communication.tcp.Server(self.__address__)
      print "server=", self.__server__
      while not self.__stop__:
        try:
          client = self.__server__.accept()
        except communication.tcp.TCPError:
          if not self.__stop__:
            print "accept failed"
          break
        with self.__clients_lock__:
          self.__clients__.append(client)
        print('client accepted: ' + str(client))
    except:
      import traceback
      print traceback.format_exc()
