import threading
import subprocess_new, subprocess
import time


def tcpdumpCmdStr(connList):
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
  def __init__(self, ip_portlist):
    threading.Thread.__init__(self)
    self.__ipportlist__ = ip_portlist
    self.stop = False
    self.nfBytes = 0
    self.__tcpdump__ = subprocess_new.Popen_events(\
      [tcpdumpCmdStr(self.__ipportlist__)], shell=True, 
      stdout = subprocess.PIPE, onStdOut=self.onStdOutHandler, onStdErr=self.onStdErrHandler)
    
  def onStdOutHandler(self, msg):
    try:
      self.nfBytes += int(msg.split()[6])
    except IndexError:
      pass
  def onStdErrHandler(self, msg):
    pass
    
  def doStop(self):
    self.stop = True
    self.__tcpdump__.terminate()
    
  def run(self):
    try:
      while self.stop == False:
        s = self.__tcpdump__.communicate()
    except:
      print "Could NOT get data from tcpdump." 
      print "tcpdump must be accessible, and you need sufficient rights for using tcpdump"
      

