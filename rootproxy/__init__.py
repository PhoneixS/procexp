"""root proxy"""

import subprocess
import os
import uuid
import const

ptoc_file = None
ctop_file = None
procroot = None

class CommandException(Exception):
  pass

def _write(f, data):
  """write to FIFO"""
  f.write(repr(data)+"\n")
  f.flush()
  
def start(asRoot = True):
  """start the command process, possible as root if required"""
  global ptoc_file
  global ctop_file
  global procroot
  
  ptoc = "/tmp/ptoc"+str(uuid.uuid4()) #ParentTOChild
  ctop = "/tmp/ctop"+str(uuid.uuid4()) #ChildTOParent
  
  os.mkfifo(ptoc) #ParentToChild
  os.mkfifo(ctop) #ChildTOParent
  
  if asRoot:
    thisFile = __file__
    thisFile = thisFile.replace(".pyc", ".py")
    procroot = subprocess.Popen(["pkexec", thisFile.replace("__init__", "procroot"), ptoc, ctop])
  else:
    procroot = subprocess.Popen([os.path.abspath(__file__).replace("__init__", "procroot"), ptoc, ctop])
    
  ptoc_file = open(ptoc, "w")
  ctop_file = open(ctop, "r")

def doCommand(CommandAndArgList):
  """issue command to procroot process and get the result"""
  global ptoc_file
  global ctop_file
  _write(ptoc_file, (const.Command.COMMAND, CommandAndArgList))
  result = eval(ctop_file.readline())
  if result[0] == const.Result.FAIL:
    raise CommandException
  else:
    return result[1]
  
def doContinuousCommand(CommandAndArgList, outputFifo):
  """execute command with stdout output to the outputFifo file name. 
     The given command keeps running."""
  global ptoc_file
  _write(ptoc_file, (const.Command.CONTINUE, CommandAndArgList, outputFifo))

def end():
  """stop procroot"""
  global ptoc_file
  _write(ptoc_file, (const.Command.END,)) 
  procroot.wait()  
