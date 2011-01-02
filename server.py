"""tcp server for procexp graphical clients"""
import utils
import threading
import communication.tcp



class ClientReceiver(object):
  """thread for receiving requests from one client"""
  def __init__(self, client, onNewData):
    self.__client__ = client
    self.__stop__ = False
    self.__cb__ = onNewData
    self.doReceive()
  
  def doStop(self):
    """stop the receiving thread"""
    self.__stop__ = True
    self.__client__.close()
    for t in self.doReceive.running:
      t.join()
      
  @utils.asynchronous(None)  
  def doReceive(self):
    """do receive from client"""
    while self.__stop__ == False:
      try:
        data = self.__client__.receive()
        self.__cb__(data)
      except:
        break


class procexpServer(object):
  """process explorer /proc server"""
  def __init__(self, address, onNewData):
    self.__clients_lock__ = threading.Lock()
    self.__address__ = address
    self.__server__ = None
    self.__clients__ = {}
    self.__stop__ = False
    self.__clientCB__ = onNewData
    
  def sendData(self, data):
    """send data to all clients"""
    popClients = []
    with self.__clients_lock__:
      for client in self.__clients__:
        try:
          client.send(data)        
        except communication.tcp.TCPError:
          #schedule for removal after send is ready.
          popClients.append(client)
        except:
          import traceback
          print traceback.format_exc()

    for client in popClients:
      self.__clients__[client].doStop()
      self.__clients__.pop(client)
      
            
  def stopServer(self):
    """stop the server"""
    self.__stop__ = True
    self.__server__.close()
    for t in self.doServe.running:
      t.join()
    for client in self.__clients__:
      self.__clients__[client].doStop()
      
  
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
          self.__clients__[client] = ClientReceiver(client, self.__clientCB__)
        print('client accepted: ' + str(client))
    except:
      import traceback
      print traceback.format_exc()
