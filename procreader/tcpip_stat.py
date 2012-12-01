import subprocess
import subprocess_new
import Queue
import threading
import datetime

TIMEOUT=10
TIMEOUTIDX=1
COUNTIDX=0
BYTESPERSECONDIDX=2

q = Queue.Queue()
_g_prevTime = None 
_g_proctcpdump = None
_g_procgrep = None

connections = {}

def _onStdOutHandler(msg):
  """stdout handler"""
  global connections
  try:
    nfbytes = int(msg[msg.rfind(" "):])
    msg = msg[3:msg.rfind(":")]
  
    if connections.has_key(msg):
      connections[msg][COUNTIDX] += nfbytes+64
      connections[msg][TIMEOUTIDX] = TIMEOUT
    else:
      connections[msg] = [nfbytes, TIMEOUT, 0]
  except ValueError:
    pass  
  
def _onStdErrHandler(msg):
  """log messages from stderr"""
    
def _start():
  global _g_proctcpdump
  global _g_procgrep
  try:
    _g_proctcpdump = subprocess.Popen(["tcpdump", "-U", "-l", "-q", "-nn", "-t" ,"-i", "any"], stdout = subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1024)
    _g_procgrep = subprocess_new.Popen_events(["grep", "-F", "IP "], bufsize=1024, \
                                              stdin=_g_proctcpdump.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
                                              onStdOut=_onStdOutHandler, onStdErr=_onStdErrHandler)
    _g_procgrep.communicate()
  except:
    import traceback
    print traceback.format_exc()

def start():
  """start measuring"""  
  threading.Thread(target=_start).start()
  
def stop():
  """stop"""
  try:
    _g_proctcpdump.kill()
    _g_procgrep.kill()
  except OSError:
    pass
  
def tick():
  global _g_prevTime
  global connections
  if _g_prevTime is None:
    _g_prevTime = datetime.datetime.now()
  else:
    now = datetime.datetime.now()
    delta = now - _g_prevTime
    _g_prevTime = now
    deltasecs = delta.seconds + delta.microseconds*1.0 / 1000000.0
    todelete = []
    for conn in connections:
      if connections[conn][TIMEOUTIDX] == 0:
        todelete.append(conn)
      else:
        connections[conn][TIMEOUTIDX] -= 1
        connections[conn][BYTESPERSECONDIDX] = int(connections[conn][COUNTIDX]*1.0 / deltasecs)
        connections[conn][COUNTIDX] = 0 
    for conn in todelete:
      connections.pop(conn)

