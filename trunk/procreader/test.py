import subprocess
import subprocess_new
import Queue
import time
import threading

TIMEOUT=10

q = Queue.Queue()

connections = {}

def onStdOutHandler(msg):
  """stdout handler"""
  global connections

  bytes = int(msg[msg.rfind(" "):])
  msg = msg[3:msg.rfind(":")]

  if connections.has_key(msg):
    connections[msg][0] += bytes+64
    connections[msg][1] = TIMEOUT
  else:
    connections[msg] = [bytes, TIMEOUT]
  
  
def onStdErrHandler(msg):
  """log messages from stderr"""
    
def start():
  try:
    proc = subprocess_new.Popen_events("tcpdump -U -l -q -nn -t -i any | grep -F 'IP '", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE, onStdOut=onStdOutHandler, onStdErr=onStdErrHandler)
    proc.communicate()
  except:
    import traceback
    print traceback.format_exc()

  
t = threading.Thread(target=start)
t.start()

while True:
  todelete = []
  for conn in connections:
    if connections[conn][1] == 0:
      todelete.append(conn)
    else:
      connections[conn][1] -= 1
    connections[conn][0] = 0 
  for conn in todelete:
    connections.pop(conn)
  time.sleep(1)
  print len(connections)
  
  for conn in connections:
    print conn, connections[conn]