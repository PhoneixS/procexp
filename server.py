"""tcp server for procexp graphical clients"""
import utils
import threading
import socket
import communication.tcp

PORTNUMBER = 4000

g_clients_lock = threading.Lock()
g_clients = []
g_address = (socket.gethostname(), 4000)
g_stop = False

def sendData(data):
  """send data to all clients"""
  with g_clients_lock:
    for client in g_clients:
      try:
        client.send(data)        
      except:
        g_clients.remove(client)
  
@utils.asynchronous(None)
def doServe():
  '''Accepts clients and adds them to list'''
  try:
    server = communication.tcp.Server(g_address)
    print "server=", server
    while not g_stop:
      try:
        client = server.accept()
      except:
        if not g_stop:
          print "accept failed"
        break
      with g_clients_lock:
        g_clients.append(client)
      print('client accepted: ' + str(client))
  except:
    import traceback
    print traceback.format_exc()
