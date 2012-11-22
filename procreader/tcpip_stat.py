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


import threading
import subprocess_new, subprocess
import shlex
import procutils

def tcpdumpCmdStr(connList):
  """generate correct command line parameters for tcpdump"""
  totalcmd = ""
  for connection in connList:
    srcaddr, srcport = connection[0]
    dstaddr, dstport = connection[1]
    if srcaddr != "0.0.0.0" and dstaddr != "0.0.0.0":
      cmd  = "\(\( host " + str(srcaddr) + " and port " + str(srcport) + " \) and "
      cmd += "\( host " + str(dstaddr) + " and port " + str(dstport) + " \)\)"
      if totalcmd == "":
        totalcmd = cmd
      else:
        totalcmd += " or " + cmd
  return "tcpdump -U -l -q -nn -i any " + totalcmd

class tcpipstat(threading.Thread):
  """This class can read tcp ip statistics"""
  def __init__(self, ip_portlist):
    threading.Thread.__init__(self)
    self.__ipportlist__ = ip_portlist
    self.stop = False
    self.nfBytes = 0
    self.__tcpdump__ = subprocess_new.Popen_events(\
      shlex.split(tcpdumpCmdStr(self.__ipportlist__)), shell=False, 
      stdout = subprocess.PIPE, stderr=subprocess.PIPE, onStdOut=self.onStdOutHandler, onStdErr=self.onStdErrHandler)
    
  def onStdOutHandler(self, msg):
    """stdout handler"""
    try:
      self.nfBytes += int(msg.split()[6])
    except IndexError:
      pass
  
  def onStdErrHandler(self, msg):
    """log messages from stderr"""
    procutils.log(msg)
    
  def doStop(self):
    """stop the tcpip stats"""
    self.stop = True
    try:
      self.__tcpdump__.terminate()
    except OSError:
      #could be already killed, ignore it
      pass
    
  def run(self):
    """run"""
    try:
      while self.stop == False:
        _ = self.__tcpdump__.communicate()
    except:
      procutils.log("Could NOT get data from tcpdump. TCPIP bytes view is not working.")
      procutils.log("tcpdump must be accessible, and you need sufficient rights for using tcpdump.")
      procutils.log("For better results, run process explorer for Linux as root.")
      

