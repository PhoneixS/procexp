# This file is part of the Linux Process Explorer
# See www.sourceforge.net/projects/procexp
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA


import os
import signal
from ctypes import *
import traceback

lib = cdll.LoadLibrary("libc.so.6")
s = create_string_buffer('\000' * 1024)

class FileError(Exception):
  pass
  
  
def readFullFileFast(path):
  
  try:
    f = lib.open(path,0)
    if f == -1: raise FileError    
      
    total = ""
      
    eof = lib.read(f, s, 1024)
    if eof == -1: raise FileError    
    if eof > 0:
      total = total + s.raw[:eof]
    
    while eof > 0:
      eof = lib.read(f, s, 1024)
      if eof == -1: raise FileError
      if eof > 0:
        total = total + s.raw[:eof]
 
    lib.close(f)
    return total
  except FileError:
    lib.close(f)
    raise
  
  except:
    print "Unhandled exception"
    print traceback.format_exc()
    raise
    
def readFullFile(path):
  return readFullFileFast(path)

def killProcess(process):
  try:
    os.kill(int(process), signal.SIGTERM)
  except OSError:
    pass
  
def killProcessHard(process):
  os.kill(int(process), signal.SIGKILL)


def humanReadable(value):
  if value < 1000:
    return str(int(value)) + " B"
  elif value >= 1000 and value < 1000000:
    return str(int(value/1000)) + " kB"
  else:
    return str(int(value/1000000)) + " MB"
