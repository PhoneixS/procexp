"""procexp reader object"""
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


#reader.py
#class which reads data from /proc

import time
import os
import utils
import subprocess
import datetime
import threading
UNKNOWN = "---"


g_passwd = None
g_pendinglddupdatesLock__ = threading.Lock() #do not refactor as part of a class, because it
                                             #is not pickable

class singleProcessDetailsAndHistory(object):
  def __init__(self, pid, historyDepth):
    self.__pid__ = str(pid)
    self.__pathPrefix__ = "/proc/"+self.__pid__+"/"
    self.__pwd__ = UNKNOWN
    self.__exepath__ = UNKNOWN
    self.__openFiles__ = {}
    self.__memMap__ = ""
    self.cpuUsageHistory = [0] * historyDepth
    self.cpuUsageKernelHistory = [0] * historyDepth
    self.rssUsageHistory = [0] * historyDepth
    self.IOHistory = [0] * historyDepth
    self.HistoryDepth = historyDepth
    self.cmdline = None
    self.startedtime = None
    self.ppid = None
  def __getOpenFileNames__(self):
    alldirs = os.listdir(self.__pathPrefix__ + "fd")
    self.__openFiles__ = {}
    for dir in alldirs:
      self.__openFiles__[dir] = {"path":os.readlink(self.__pathPrefix__ + dir)}
  def update(self, cpuUsage, cpuUsageKernel, totalRss, IO):
    if cpuUsage > 100:
      cpuUsage = 0
    if cpuUsageKernel > 100:
      cpuUsageKernel = 0
    if self.__pwd__ == UNKNOWN:
      try:
        self.__pwd__ = os.readlink(self.__pathPrefix__ + "cwd")
      except:
        self.__pwd__ = UNKNOWN
    self.cpuUsageHistory.append(cpuUsage)
    self.cpuUsageKernelHistory.append(cpuUsageKernel)
    self.rssUsageHistory.append(totalRss)
    self.IOHistory.append(IO)
    
    self.cpuUsageHistory = self.cpuUsageHistory[1:]
    self.cpuUsageKernelHistory = self.cpuUsageKernelHistory[1:]
    self.rssUsageHistory = self.rssUsageHistory[1:]
    self.IOHistory = self.IOHistory[1:]

    
    try:
      self.cwd = os.readlink(self.__pathPrefix__ + "cwd")
    except OSError, val:
      self.cwd = "<"+val.strerror+">"
    except :
      raise

    if self.cmdline == None:
      #do below only once
      try:
        self.cmdline = utils.readFullFile(self.__pathPrefix__ + "cmdline").replace("\x00"," ")
      except OSError, val:
        self.cmdline = "<"+val.strerror+">"
      except utils.FileError:
        self.cmdline = "---"
      except:
        raise
    
    try:
      self.exe = os.readlink(self.__pathPrefix__ + "exe")
    except OSError, val:
      self.exe = "<"+val.strerror+">"
    except :
      raise
    
    #started time of a process
    if self.startedtime == None:
      try:
        procstartedtime_seconds = utils.readFullFile(self.__pathPrefix__ + "stat").split(" ")[21]
      
      
        procstat = utils.readFullFile("/proc/stat").split("\n")
        for line in procstat:
          if line.find("btime") != -1:
            systemstarted_seconds = line.split(" ")[1]
        HZ = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        epoch = datetime.datetime(month=1,day=1,year=1970)
        
        
        procstarted = epoch + \
                      datetime.timedelta(seconds=int(systemstarted_seconds)) + \
                      datetime.timedelta(seconds=int(int(procstartedtime_seconds)/(HZ*1.0)+0.5))
        
        self.startedtime = procstarted.strftime("%A, %d. %B %Y %I:%M%p")
      except utils.FileError:
        self.startedtime = "--"
      
    #process parent pid
    if self.ppid is None:
      try:
        self.ppid = utils.readFullFile(self.__pathPrefix__ + "stat").split(" ")[3]
      except utils.FileError:
        self.ppid = None
  def do_ldd(self):
    print self.__pid__, "do_ldd: create ldd method here!!"
    

class _cpuActivityReader(object):
  """class for reading acivity per cpu"""
  def __init__(self, cpu):
    self.__cpu__ = cpu
    self.__prevUserMode__ = None
    self.__prevUserNiceMode__ = None
    self.__prevSystemMode__ = None
    self.__prevIdleMode__ = None
    self.__prevIoWait__ = None
    self.__prevIrqMode__ = None
    self.__prevSoftIrqMode__ = None
    self.__deltaUserMode__ = None
    self.__deltaUserMode__ = None
    self.__deltaUserNiceMode__ = None
    self.__deltaSystemMode__ = None
    self.__deltaIdleMode__ = None
    self.__deltaIoWait__ = None
    self.__deltaIrqMode__ = None
    self.__deltaSoftIrqMode__ = None
    self.__newjiffies = None
    self.__overallUserCpuUsage__ = None
    self.__overallSystemCpuUsage__ = None
    self.__overallIoWaitCpuUsage__ = None
    self.__overallIrqCpuUsage__ = None
    
    
    
  def update(self):
    """do an update from the /proc filesystem """
    jiffyStr = utils.readFullFile('/proc/stat').split("\n")[self.__cpu__+1]
    userMode = int(jiffyStr.split()[1])
    userNiceMode = int(jiffyStr.split()[2])
    systemMode = int(jiffyStr.split()[3])
    idleMode = int(jiffyStr.split()[4]) 
    
    ioWait = int(jiffyStr.split()[5])
    irqMode = int(jiffyStr.split()[6])
    softIrqMode = int(jiffyStr.split()[7])
    
    self.__newjiffies = userMode + userNiceMode + \
                        systemMode + idleMode + ioWait + irqMode + softIrqMode
     
    if self.__deltaUserMode__ == None:
      self.__prevUserMode__ = userMode
      self.__prevUserNiceMode__ = userNiceMode
      self.__prevSystemMode__ = systemMode
      self.__prevIdleMode__ = idleMode
      self.__prevIoWait__ = ioWait
      self.__prevIrqMode__ = irqMode
      self.__prevSoftIrqMode__ = softIrqMode
      
      self.__deltaUserMode__ = 0
      self.__deltaUserNiceMode__ = 0
      self.__deltaSystemMode__ = 0
      self.__deltaIdleMode__ = 0
      self.__deltaIoWait__ = 0
      self.__deltaIrqMode__ = 0
      self.__deltaSoftIrqMode__ = 0
      
    else:
      self.__deltaUserMode__ = userMode - self.__prevUserMode__
      self.__deltaUserNiceMode__ = userNiceMode - self.__prevUserNiceMode__
      self.__deltaSystemMode__ = systemMode - self.__prevSystemMode__
      self.__deltaIdleMode__ = idleMode - self.__prevIdleMode__
      self.__deltaIoWait__ = ioWait - self.__prevIoWait__
      self.__deltaIrqMode__ = irqMode - self.__prevIrqMode__
      self.__deltaSoftIrqMode__ = softIrqMode - self.__prevSoftIrqMode__
      
      
      self.__prevUserMode__ = userMode
      self.__prevUserNiceMode__ = userNiceMode
      self.__prevSystemMode__ = systemMode
      self.__prevIdleMode__ = idleMode
      self.__prevIoWait__ = ioWait
      self.__prevIrqMode__ = irqMode
      self.__prevSoftIrqMode__ = softIrqMode
      
    
    
    total = float(self.__deltaUserMode__ + 
            self.__deltaUserNiceMode__ + 
            self.__deltaSystemMode__ + 
            self.__deltaIdleMode__ +
            self.__deltaIoWait__ +
            self.__deltaIrqMode__ +
            self.__deltaSoftIrqMode__)
    
    self.__overallUserCpuUsage__    = \
      round(((self.__deltaUserMode__ + self.__deltaUserNiceMode__)*1.0 / total)*100, 1) \
      if total > 0 else 0
    self.__overallSystemCpuUsage__  = \
      round((self.__deltaSystemMode__ *1.0 / total)*100, 1) \
      if total > 0 else 0
    self.__overallIoWaitCpuUsage__  = \
      round((self.__deltaIoWait__*1.0 / total)*100, 1) \
      if total > 0 else 0
    self.__overallIrqCpuUsage__     = \
      round(((self.__deltaIrqMode__ + self.__deltaSoftIrqMode__) *1.0 / total)*100, 1) \
      if total > 0 else 0
    
  def overallUserCpuUsage(self):
    """get cpu usage for all cpu's""" 
    return self.__overallUserCpuUsage__
  def overallSystemCpuUsage(self):
    """get overall system usage for all cpus"""
    return self.__overallSystemCpuUsage__
  def overallIoWaitCpuUsage(self):
    """get io wait usage for all cpus"""
    return self.__overallIoWaitCpuUsage__
  def overallIrqCpuUsage(self):
    """ get irq usage for all cpus"""
    return self.__overallIrqCpuUsage__
  def newjiffies(self):
    """get the new jiffies count"""
    return self.__newjiffies
 
class procreader(object): #pylint: disable-msg=R0902
  """class for reading process and cpu accounting values"""
  def __init__(self, timerValue, historyCount):
    self.__initReader__()
    self.__uidFilter__ = None
    self.__updateTimer__ = timerValue
    self.__historyCount__ = historyCount
    self.__allcpu__ = _cpuActivityReader(-1)
    self.__processList__ = {}
    self.__closedProcesses__ = None
    self.__newProcesses__ = None
    self.__prevJiffies__ = None
    self.__deltaJiffies__ = None
    self.__overallUserCpuUsage__ = 0
    self.__overallSystemCpuUsage__  = 0
    self.__allConnections__ = {}
    self.__allUDP__ = {}
    self.__totalMemKb   = 0
    self.__actualMemKb  = 0
    self.__buffersMemKb = 0
    self.__cachedMemKb  = 0
    self.__loadavg__ = 0
    self.__noofprocs__ = 0
    self.__noofrunningprocs__ = 0
    self.__lastpid__ = 0
    self.__pendinglddupdates__ = []
    
         
    cpuinfo = utils.readFullFile("/proc/cpuinfo").split("\n")
    self.__cpuCount__ = 0
    self.__networkCards__= {}
    self.__cpuArray__ = []
    self.__prevTimeStamp__ = None
    for line in cpuinfo:
      if line.startswith("processor"):
        self.__cpuArray__.append(_cpuActivityReader(self.__cpuCount__))
        self.__cpuCount__ += 1
    
    #network cards
    data = utils.readFullFile('/proc/net/dev').split("\n")[2:]
    for line in data:
      cardName = line.split(":")[0].strip()
      if len(cardName) > 0:
        self.__networkCards__[cardName] = {"actual":[0, 0, 0, 0],  #in/s out/s previn, prevout]
                                           "speed":None}
    #try to find speeds if ethtool is available and accessible
    print "network card speed detection results"
    print "------------------------------------"
    
    ethtoolerror = False
    for card in self.__networkCards__:
      speed = None
      try:
        ethtool = subprocess.Popen(["ethtool", card], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        data = ethtool.communicate()
      except:
        ethtoolerror = True
      
      try:
        if data[0] is not None:
          for line in data[0].split("\n"):
            if line.find("Speed") != -1: 
              speed = int(line.split(":")[1].split("Mb/s")[0])
      #except subprocess.child_exception:
      #  print "  For better results, allow rights to ethtool, and/or run as root"        
      #  speed = None
      except :
        speed = None
      
      if speed is not None:
        print "  ethernet device", card, "has speed", speed, "Mb/s according to ethtool"
        self.__networkCards__[card]["speed"] = speed
      else:
        print "  ethernet device", card, "has unknown speed"
        print "  network graph scaling for", card, "is set to autoscale"
    if ethtoolerror:
      print "  ** ethtool not found, or access denied. For better results, allow access to ethtool"
      
  def __repr__(self):
    s = "procreader instance: #proc=" + str(len(self.__processList__)) + "\n" + \
        "#processors:" + str(len(self.__cpuArray__))
    return s 

  def __initReader__(self):
    self.__processList__ = {}
    self.__closedProcesses__ = None
    self.__newProcesses__ = None
    self.__prevJiffies__ = None
    self.__deltaJiffies__ = None
    
    self.__overallUserCpuUsage__ = 0
    self.__overallSystemCpuUsage__  = 0
    
  def __getGlobalJiffies__(self):
    newjiffies = self.__allcpu__.newjiffies()
    if self.__deltaJiffies__ == None:
      self.__prevJiffies__ = newjiffies
      self.__deltaJiffies__ = 1
    else:
      self.__deltaJiffies__ = newjiffies - self.__prevJiffies__
      self.__prevJiffies__ = newjiffies    
  
  def __updateCPUs__(self):
    self.__allcpu__.update()
    for cpu in self.__cpuArray__:
      cpu.update()

  def __update_all_ldd__(self):
    with g_pendinglddupdatesLock__:
      for process in self.__pendinglddupdates__: 
        if self.__processList__.has_key(int(process)):
          self.__processList__[int(process)]["history"].do_ldd()
      self.__pendinglddupdates__ = []
      
    
  
  def overallUserCpuUsage(self):
    """get overallUserCpuUsage"""
    return self.__allcpu__.overallUserCpuUsage()
  def overallSystemCpuUsage(self):
    """get overallSystemCpuUsage"""
    return self.__allcpu__.overallSystemCpuUsage()
  def overallIoWaitCpuUsage(self):
    """get overallIoWaitCpuUsage"""
    return self.__allcpu__.overallIoWaitCpuUsage()
  def overallIrqCpuUsage(self):
    """get overallIrqCpuUsage"""
    return self.__allcpu__.overallIrqCpuUsage()
    
  def getSingleCpuUsage(self, cpu):
    """get usage for one CPU """
    data = (self.__cpuArray__[cpu].overallUserCpuUsage(),
           self.__cpuArray__[cpu].overallSystemCpuUsage(),
           self.__cpuArray__[cpu].overallIoWaitCpuUsage(),
           self.__cpuArray__[cpu].overallIrqCpuUsage())
    return data

    
  def setFilterUID(self, uid):
    """filter the processes, only use those of the given UID"""
    self.__uidFilter__ = uid
    self.__initReader__()
    
  def noFilterUID(self):
    """do not filter"""
    self.__uidFilter__ = None
    self.__initReader__()
    
  def getProcUid(self, proc):#pylint: disable-msg=R0201
    """get UID of given proc"""
    try:
      uid = os.stat("/proc/"+proc).st_uid
    except OSError:
      uid = 0
    return uid
    
  def __getAllProcesses__(self):
    alldirs = os.listdir("/proc")   
    
    if self.__uidFilter__ != None:
      newProcessSetAll = [ process for process in alldirs if process.isdigit() ]
      newProcessList = [ int(process) for process in newProcessSetAll \
                        if self.getProcUid(process) == self.__uidFilter__ ]
      #newProcessList.append(1)
      newProcessSet=set(newProcessList)
        
    else:
      newProcessSet = set([ int(process) for process in alldirs if process.isdigit() ])
    
    oldProcessSet = set([ process for process in self.__processList__ ])
    
    self.__closedProcesses__ = oldProcessSet.difference(newProcessSet)
    self.__newProcesses__ = newProcessSet.difference(oldProcessSet)
    
    for process in self.__closedProcesses__:
      del self.__processList__[process]
      
    for process in self.__newProcesses__:
      self.__processList__[process] = {"name": "", \
        "env": UNKNOWN, \
        "prevJiffy":0, \
        "prevJiffyKernel":0, \
        "prevIO":0, \
        "PPID":None, \
        "cpuUsage":0, \
        "cmdline" : UNKNOWN, \
        "uid":UNKNOWN, \
        "wchan":UNKNOWN, \
        "nfThreads":UNKNOWN, \
        "history":singleProcessDetailsAndHistory(process, self.__historyCount__)}

  def __getUIDName__(self, uid): #pylint: disable-msg=R0201
    global g_passwd #pylint: disable-msg=W0603
    if g_passwd is None:
      g_passwd = utils.readFullFile("/etc/passwd").split("\n")
    name = "???"
    for line in g_passwd:
      try:
        if line.split(":")[2] == uid:
          name = line.split(":")[0]
      except:
        pass
    return name
    
    
  def __removeUnknownParents__(self):#useful when filtered on UID
    for process in self.__processList__:
      if self.__processList__[process]["PPID"] > 0:
        if not(self.__processList__.has_key(self.__processList__[process]["PPID"])):
          self.__processList__[process]["PPID"] = 0

  def __getProcessDetails__(self):
    for process in self.__processList__:
      if self.__processList__[process]["env"] == UNKNOWN:
        try:
          env = utils.readFullFile("/proc/"+str(process)+"/environ").split("\0")
        except:
          env = '-'
        self.__processList__[process]["env"] = env
      
  def __getProcessCpuDetails__(self):
    for process in self.__processList__:
      procStat = None
      try:
        procStat = utils.readFullFile("/proc/"+str(process)+"/stat")
        if self.__processList__[process]["cmdline"] == UNKNOWN:
          cmdLine = utils.readFullFile("/proc/"+str(process)+"/cmdline")
          self.__processList__[process]["cmdline"] = cmdLine.replace("\x00"," ")

        #get UID of process
        if self.__processList__[process]["uid"] == UNKNOWN:
          uid = str(os.stat("/proc/"+str(process))[4])
          self.__processList__[process]["uid"] = self.__getUIDName__(uid)        
      except:
        pass
      
      try:    
        statm = utils.readFullFile("/proc/"+str(process)+"/statm")
        totalRssMem = int(statm.split(' ')[1])*4 #in 4k pages

        #smaps = utils.readFullFile("/proc/"+str(process)+"/smaps").split("kB\nRss:")
        #totalRssMem = 0
        #for line in smaps:
          #if line.startswith(" "):
            #totalRssMem += int(line.split("kB")[0].strip())
            
      except:
        totalRssMem = 0
        
      try:
        wchan = utils.readFullFile("/proc/"+str(process)+"/wchan")
        self.__processList__[process]["wchan"] = wchan
      except:
        self.__processList__[process]["wchan"] = UNKNOWN
        
          
        
      if procStat != None:
        procStatSplitted = procStat.split()
        nextJiffy = int(procStatSplitted[13]) + int(procStatSplitted[14])
        try:
          cpuUsage = round(((nextJiffy - self.__processList__[process]["prevJiffy"]) / 
                            (self.__deltaJiffies__ * 1.0)) * 100, 1)
        except ZeroDivisionError:
          cpuUsage = 0.0
        
        nextJiffyKernel = int(procStatSplitted[14])
        try:
          cpuUsageKernel = round(
            ((nextJiffyKernel - self.__processList__[process]["prevJiffyKernel"]) / 
             (self.__deltaJiffies__ * 1.0)) * 100, 1)
        except ZeroDivisionError:
          cpuUsageKernel = 0
        #IO accounting
        try:
          io = utils.readFullFile("/proc/"+str(process)+"/io").split("\n")
          iototal = int(io[0].split(": ")[1]) + int(io[1].split(": ")[1])
        except:
          iototal = 0
        
        if self.__processList__[process]["prevIO"] == 0: #first time
          deltaio = 0
        else:
          deltaio = iototal - self.__processList__[process]["prevIO"]
        self.__processList__[process]["prevIO"] = iototal
        
        self.__processList__[process]["cpuUsage"] = cpuUsage
        self.__processList__[process]["prevJiffy"] = nextJiffy
        self.__processList__[process]["cpuUsageKernel"] = cpuUsageKernel
        self.__processList__[process]["prevJiffyKernel"] = nextJiffyKernel
        self.__processList__[process]["PPID"] = int(procStatSplitted[3])
        self.__processList__[process]["name"] = procStatSplitted[1]
        
        self.__processList__[process]["Rss"] = totalRssMem
        self.__processList__[process]["history"].update(cpuUsage, 
                                                        cpuUsageKernel, 
                                                        totalRssMem, 
                                                        deltaio/1024)
        self.__processList__[process]["nfThreads"] = procStatSplitted[19]
      else:
        self.__processList__[process]["PPID"] = 1
        
  #def getIOAccounting():
  #  pass
    #~ Description
    #~ -----------

    #~ rchar: (unsigned long long)

    #~ The number of bytes which this task has caused to be read from storage.
    #~ This is simply the sum of bytes which this process passed to read() and
    #~ pread(). It includes things like tty IO and it is unaffected by whether
    #~ or not actual physical disk IO was required (the read might have been
    #~ satisfied from pagecache)


    #~ wchar: (unsigned long long)

    #~ The number of bytes which this task has caused, or shall cause to be written
    #~ to disk. Similar caveats apply here as with rchar.


    #~ syscr: (unsigned long long)

    #~ I/O counter: read syscalls
    #~ Attempt to count the number of read I/O operations, i.e. syscalls like read()
    #~ and pread().


    #~ syscw: (unsigned long long)

    #~ I/O counter: write syscalls
    #~ Attempt to count the number of write I/O operations, i.e. syscalls like write()
    #~ and pwrite().


    #~ read_bytes: (unsigned long long)

    #~ I/O counter: bytes read
    #~ Attempt to count the number of bytes which this process really did cause to
    #~ be fetched from the storage layer. Done at the submit_bio() level, so it is
    #~ accurate for block-backed filesystems. <please add status regarding NFS and CIFS
    #~ at a later time>


    #~ write_bytes: (unsigned long long)

    #~ I/O counter: bytes written
    #~ Attempt to count the number of bytes which this process caused to be sent to
    #~ the storage layer. This is done at page-dirtying time.


    #~ cancelled_write_bytes: (unsigned long long)

    #~ The big inaccuracy here is truncate. If a process writes 1MB to a file and
    #~ then deletes the file, it will in fact perform no writeout. But it will have
    #~ been accounted as having caused 1MB of write.
    #~ In other words: The number of bytes which this process caused to not happen,
    #~ by truncating pagecache. A task can cause "negative" IO too. If this task
    #~ truncates some dirty pagecache, some IO which another task has been accounted
    #~ for (in its write_bytes) will not be happening. We _could_ just subtract that
    #~ from the truncating task's write_bytes, but there is information loss in doing
    #~ that.


    #~ Note:

    #~ At it`s current implementation state, it's a bit racy on 32-bit machines: if process
    #~ A reads process B's /proc/pid/io while process B is updating one of those 64-bit
    #~ counters, process A could see an intermediate result.    
  def __getAllSocketInfo__(self):
    self.__allConnections__ = {} #list of connections, organized by inode
    data = utils.readFullFile("/proc/net/tcp").split("\n")
    for connection in data:
      if len(connection) > 1:
        self.__allConnections__[connection.split()[9]] = connection.split()
  def __getAllUDPInfo__(self):
    self.__allUDP__ = {} #list of connections, organized by inode
    data = utils.readFullFile("/proc/net/udp").split("\n")
    for udp in data:
      if len(udp) > 1:
        self.__allUDP__[udp.split()[9]] = udp.split()

  def __getMemoryInfo(self):
    """get memory info"""
    mem = utils.readFullFile("/proc/meminfo").split("\n")
    self.__totalMemKb   = int(mem[0].split()[1])
    self.__actualMemKb  = int(mem[1].split()[1])
    self.__buffersMemKb = int(mem[2].split()[1])
    self.__cachedMemKb  = int(mem[3].split()[1])
  
  def __getAverageLoad(self):
    """get average load figures"""
    load = utils.readFullFile("/proc/loadavg").split()
    self.__loadavg__ = (load[0], load[1], load[2])
    self.__noofprocs__ = load[3].split("/")[1]
    self.__noofrunningprocs__ = load[3].split("/")[0]
    self.__lastpid__ = load[4]
    
    
  def getNetworkCards(self):
    """return onfo about available network interfaces"""
    return self.__networkCards__

  def getNetworkCardUsage(self, cardName):
    """get network usage figures"""
    return self.__networkCards__[cardName]["actual"][0], \
      self.__networkCards__[cardName]["actual"][1]
  
  def getNetworkCardData(self, cardName):
    """getNetworkCardData"""
    return self.__networkCards__[cardName]
    
  def getAllProcessSockets(self, process):
    """get all sockets of a process""" 
    allFds = {}
    allUDP = {}
    try:
      __allFds = os.listdir("/proc/" + str(process) + "/fd")
    except:
      __allFds = ""
    for fd in __allFds:
      try:
        link = os.readlink("/proc/" + str(process) + "/fd/" + fd)
      except:
        link = ""
      if link.startswith("socket"):
        inode = link.split("[")[1].split("]")[0]
        try:
          allFds[inode] = self.__allConnections__[inode]
        except:
          pass
        try:
          allUDP[inode] = self.__allUDP__[inode]
        except:
          pass
    return allFds, allUDP
    
  def __getNetworkCardUsage(self):
    """get usage of network interfaces"""
    data = utils.readFullFile('/proc/net/dev').split("\n")[2:]
    actTime = time.time()
    for line in data:
      cardName = line.split(":")[0].strip()
      if len(cardName) > 0:
        splittedLine = line.split(":")[1].split()
        recv = int(splittedLine[0])
        sent = int(splittedLine[8])

        if self.__prevTimeStamp__ != None:
          if self.__networkCards__[cardName]["actual"][2] == 0:
            pass
          else:
            self.__networkCards__[cardName]["actual"][0] = \
              (recv - self.__networkCards__[cardName]["actual"][2]) / \
                (actTime - self.__prevTimeStamp__)
            self.__networkCards__[cardName]["actual"][1] = \
              (sent - self.__networkCards__[cardName]["actual"][3]) / \
                (actTime - self.__prevTimeStamp__)
          if self.__networkCards__[cardName]["actual"][0] <0:
            self.__networkCards__[cardName]["actual"][0] = 0
          if self.__networkCards__[cardName]["actual"][1] <0:
            self.__networkCards__[cardName]["actual"][1] = 0
            
          self.__networkCards__[cardName]["actual"][2] = recv
          self.__networkCards__[cardName]["actual"][3] = sent
        
        self.__networkCards__[cardName]["recerrors"]  = int(splittedLine[2])
        self.__networkCards__[cardName]["recdrops"]   = int(splittedLine[3])
        self.__networkCards__[cardName]["senderrors"] = int(splittedLine[10])
        self.__networkCards__[cardName]["senddrops"]  = int(splittedLine[11])
        self.__networkCards__[cardName]["sendcoll"]   = int(splittedLine[13])
        self.__networkCards__[cardName]["recbytes"]   = int(splittedLine[0])        
        self.__networkCards__[cardName]["recpackets"]   = int(splittedLine[1])        
        self.__networkCards__[cardName]["sendbytes"]   = int(splittedLine[8])        
        self.__networkCards__[cardName]["sendpackets"]   = int(splittedLine[9])        
        
          
  
  def doReadProcessInfo(self):
    """read all info from /proc and store it in the object data area"""
    self.__updateCPUs__()
    self.__getGlobalJiffies__()
    self.__getAllProcesses__()
    self.__getProcessCpuDetails__()
    self.__removeUnknownParents__()
    self.__getProcessDetails__()
    self.__getAllSocketInfo__()
    self.__getAllUDPInfo__()
    self.__getMemoryInfo()
    self.__getAverageLoad()
    self.__getNetworkCardUsage()
    #keep line below as last command
    self.__prevTimeStamp__ = time.time()
    self.__update_all_ldd__()
    
  def getProcessInfo(self):
    """get process info of all current processes, filtered possible by UID"""
    return self.__processList__
  def hasProcess(self, process):
    """check if given process exists"""
    return self.__processList__.has_key(int(process))
  def getProcessCpuUsageHistory(self, process):
    """get usage history of given process""" 
    return self.__processList__[int(process)]["history"].cpuUsageHistory
  def getcwd(self, process):
    """get curr dir of process"""
    return self.__processList__[int(process)]["history"].cwd
  def getexe(self, process):
    """get exe name of process"""
    return self.__processList__[int(process)]["history"].exe
  def getstartedtime(self, process):
    """get the time started for a process"""
    return self.__processList__[int(process)]["history"].startedtime
  def getcmdline(self, process):
    """get the command line of a process"""
    return self.__processList__[int(process)]["history"].cmdline
  def getppid(self, process):
    """get parent pid of a process"""
    return self.__processList__[int(process)]["history"].ppid
  def getProcessCpuUsageKernelHistory(self, process):
    """get the kernel usage history of a process"""
    return self.__processList__[int(process)]["history"].cpuUsageKernelHistory
  def getProcessRssUsageHistory(self, process):
    """getProcessRssUsageHistory"""
    return self.__processList__[int(process)]["history"].rssUsageHistory
  def getIOHistory(self, process):
    """get IO history of a process"""
    return self.__processList__[int(process)]["history"].IOHistory
  def getEnvironment(self, process):
    """get environment of a process"""
    return self.__processList__[int(process)]["env"]
  def getHistoryDepth(self, process):
    """get history depth of a process"""
    return self.__processList__[int(process)]["history"].HistoryDepth
  def getCpuCount(self):
    """get number of cpus"""
    return self.__cpuCount__
  def getMemoryUsage(self):
    """get memory usage totals"""
    return self.__totalMemKb, self.__actualMemKb, self.__buffersMemKb, self.__cachedMemKb
  def getLoadAvg(self):
    """get load average totals"""
    return  self.__loadavg__, self.__noofprocs__, self.__noofrunningprocs__, self.__lastpid__
  def update_lddinfo(self, process):
    """initiate an update of ldd info of given process"""
    with g_pendinglddupdatesLock__:
      self.__pendinglddupdates__.append(process)

