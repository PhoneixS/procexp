#reader.py
#class which reads data from /proc

import time
import os
import procutils
import copy
import singleprocess
import binascii

UNKNOWN = "---"


g_passwd = None

class cpuhistoryreader(object):
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
    
  def update(self):
    jiffyStr = procutils.readFullFile('/proc/stat').split("\n")[self.__cpu__+1]
    userMode = int(jiffyStr.split()[1])
    userNiceMode = int(jiffyStr.split()[2])
    systemMode = int(jiffyStr.split()[3])
    idleMode = int(jiffyStr.split()[4]) 
    
    ioWait = int(jiffyStr.split()[5])
    irqMode = int(jiffyStr.split()[6])
    softIrqMode = int(jiffyStr.split()[7])
    
    self.__newjiffies = userMode + userNiceMode + systemMode + idleMode + ioWait + irqMode + softIrqMode
     
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
    
    self.__overallUserCpuUsage__    = round(((self.__deltaUserMode__ + self.__deltaUserNiceMode__)*1.0 / total)*100, 1) if total > 0 else 0
    self.__overallSystemCpuUsage__  = round((self.__deltaSystemMode__ *1.0 / total)*100, 1) if total > 0 else 0
    self.__overallIoWaitCpuUsage__  = round((self.__deltaIoWait__*1.0 / total)*100, 1) if total > 0 else 0
    self.__overallIrqCpuUsage__     = round(((self.__deltaIrqMode__ + self.__deltaSoftIrqMode__) *1.0 / total)*100, 1) if total > 0 else 0
      
  def overallUserCpuUsage(self):
    return self.__overallUserCpuUsage__
  def overallSystemCpuUsage(self):
    return self.__overallSystemCpuUsage__
  def overallIoWaitCpuUsage(self):
    return self.__overallIoWaitCpuUsage__
  def overallIrqCpuUsage(self):
    return self.__overallIrqCpuUsage__
  def newjiffies(self):
    return self.__newjiffies
 
class procreader(object):
  def __init__(self, timerValue, historyCount):
    self.__initReader__()
    self.__uidFilter__ = None
    self.__updateTimer__ = timerValue
    self.__historyCount__ = historyCount
    self.__allcpu__ = cpuhistoryreader(-1)
    
    cpuinfo = procutils.readFullFile("/proc/cpuinfo").split("\n")
    self.__cpuCount__ = 0
    self.__networkCardCount__=0
    self.__cpuArray__ = []
    self.__networkCardArray__ = []
    for line in cpuinfo:
      if line.startswith("processor"):
        self.__cpuArray__.append(cpuhistoryreader(self.__cpuCount__))
        self.__cpuCount__ += 1
    
    #network cards
    self.__networkCardCount__ = len(procutils.readFullFile('/proc/net/dev').split("\n"))-3
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
  
  def __updateCPUs(self):
    self.__allcpu__.update()
    for cpu in self.__cpuArray__:
      cpu.update()

  def __updateNetworkCards(self):
    for card in self.__networkCardArray__:
      card.update()
  
  def overallUserCpuUsage(self):
    return self.__allcpu__.overallUserCpuUsage()
  def overallSystemCpuUsage(self):
    return self.__allcpu__.overallSystemCpuUsage()
  def overallIoWaitCpuUsage(self):
    return self.__allcpu__.overallIoWaitCpuUsage()
  def overallIrqCpuUsage(self):
    return self.__allcpu__.overallIrqCpuUsage()
    
  def getSingleCpuUsage(self, cpu):
    data = (self.__cpuArray__[cpu].overallUserCpuUsage(),
           self.__cpuArray__[cpu].overallSystemCpuUsage(),
           self.__cpuArray__[cpu].overallIoWaitCpuUsage(),
           self.__cpuArray__[cpu].overallIrqCpuUsage())
    return data

    
  def setFilterUID(self,uid):
    self.__uidFilter__ = uid
    self.__initReader__()
    
  def noFilterUID(self):
    self.__uidFilter__ = None
    self.__initReader__()
    
  def getProcUid(self,proc):
    try:
      uid = os.stat("/proc/"+proc).st_uid
    except OSError:
      uid = 0
    return uid
    
  def __getAllProcesses__(self):
    alldirs = os.listdir("/proc")   
    
    if self.__uidFilter__ != None:
      newProcessSetAll = [ process for process in alldirs if process.isdigit() ]
      newProcessList = [ int(process) for process in newProcessSetAll if self.getProcUid(process) == self.__uidFilter__ ]
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
                                      "history":singleprocess.singleProcessDetailsAndHistory(process,self.__historyCount__)}

  def __getUIDName__(self, uid):
    global g_passwd
    if g_passwd is None:
      g_passwd = procutils.readFullFile("/etc/passwd").split("\n")
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
          env = procutils.readFullFile("/proc/"+str(process)+"/environ").split("\0")
        except:
          env = '-'
        self.__processList__[process]["env"] = env
      
  def __getProcessCpuDetails__(self):
    for process in self.__processList__:
      try:
        procStat = procutils.readFullFile("/proc/"+str(process)+"/stat")
        if self.__processList__[process]["cmdline"] == UNKNOWN:
          cmdLine = procutils.readFullFile("/proc/"+str(process)+"/cmdline")
          self.__processList__[process]["cmdline"] = cmdLine.replace("\x00"," ")

        #get UID of process
        if self.__processList__[process]["uid"] == UNKNOWN:
          uid = str(os.stat("/proc/"+str(process))[4])
          self.__processList__[process]["uid"] = self.__getUIDName__(uid)        
      except:
        pass
      
      try:    
        statm = procutils.readFullFile("/proc/"+str(process)+"/statm")
        totalRssMem = int(statm.split(' ')[1])*4 #in 4k pages

        #smaps = procutils.readFullFile("/proc/"+str(process)+"/smaps").split("kB\nRss:")
        #totalRssMem = 0
        #for line in smaps:
          #if line.startswith(" "):
            #totalRssMem += int(line.split("kB")[0].strip())
            
      except:
        totalRssMem = 0
        
      try:
        wchan = procutils.readFullFile("/proc/"+str(process)+"/wchan")
        self.__processList__[process]["whan"] = wchan
      except:
        self.__processList__[process]["whan"] = UNKNOWN
        
          
        
      if procStat != None:
        procStatSplitted = procStat.split()
        nextJiffy = int(procStatSplitted[13]) + int(procStatSplitted[14])
        try:
          cpuUsage = round(((nextJiffy - self.__processList__[process]["prevJiffy"]) / (self.__deltaJiffies__ * 1.0)) * 100, 1)
        except ZeroDivisionError:
          cpuUsage = 0.0
        
        nextJiffyKernel = int(procStatSplitted[14])
        try:
          cpuUsageKernel = round(((nextJiffyKernel - self.__processList__[process]["prevJiffyKernel"]) / (self.__deltaJiffies__ * 1.0)) * 100, 1)
        except ZeroDivisionError:
          cpuUsageKernel = 0
        #IO accounting
        try:
          io = procutils.readFullFile("/proc/"+str(process)+"/io").split("\n")
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
        self.__processList__[process]["history"].update(cpuUsage, cpuUsageKernel, totalRssMem, deltaio/1024)
        self.__processList__[process]["nfThreads"] = procStatSplitted[19]
      else:
        self.__processList__[process]["PPID"] = 1
        
  def getIOAccounting():
    pass
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
    data = procutils.readFullFile("/proc/net/tcp").split("\n")
    for connection in data:
      if len(connection) > 1:
        self.__allConnections__[connection.split()[9]] = connection.split()
  def __getAllUDPInfo__(self):
    self.__allUDP__ = {} #list of connections, organized by inode
    data = procutils.readFullFile("/proc/net/udp").split("\n")
    for udp in data:
      if len(udp) > 1:
        self.__allUDP__[udp.split()[9]] = udp.split()

  def __getMemoryInfo(self):
    mem = procutils.readFullFile("/proc/meminfo").split("\n")
    self.__totalMemKb   = int(mem[0].split()[1])
    self.__actualMemKb  = int(mem[1].split()[1])
    self.__buffersMemKb = int(mem[2].split()[1])
    self.__cachedMemKb  = int(mem[3].split()[1])
  
  def __getAverageLoad(self):
    load = procutils.readFullFile("/proc/loadavg").split()
    self.__loadavg__ = (load[0],load[1],load[2])
    self.__noofprocs__ = load[3].split("/")[1]
    self.__noofrunningprocs__ = load[3].split("/")[0]
    self.__lastpid__ = load[4]
    
    
  def getNetworkCardCount(self):
    return self.__networkCardCount__

  def getNetworkCardUsage(self, card):
    return 0,20
    
  def getAllProcessSockets(self,process):
    
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
  
  def doReadProcessInfo(self):
    self.__updateCPUs()
    self.__updateCPUs()
    self.__getGlobalJiffies__()
    self.__getAllProcesses__()
    self.__getProcessCpuDetails__()
    self.__removeUnknownParents__()
    self.__getProcessDetails__()
    self.__getAllSocketInfo__()
    self.__getAllUDPInfo__()
    self.__getMemoryInfo()
    self.__getAverageLoad()
    
  def getProcessInfo(self):
    return self.__processList__, self.__closedProcesses__, self.__newProcesses__

  def hasProcess(self, process):
    return self.__processList__.has_key(int(process))
  def getProcessCpuUsageHistory(self, process):
    return self.__processList__[int(process)]["history"].cpuUsageHistory
  def getProcessCpuUsageKernelHistory(self, process):
    return self.__processList__[int(process)]["history"].cpuUsageKernelHistory
  def getProcessRssUsageHistory(self, process):
    return self.__processList__[int(process)]["history"].rssUsageHistory
  def getIOHistory(self, process):
    return self.__processList__[int(process)]["history"].IOHistory
  def getEnvironment(self,process):
    return self.__processList__[int(process)]["env"]
  def getHistoryDepth(self, process):
    return self.__processList__[int(process)]["history"].HistoryDepth
  def getCpuCount(self):
    return self.__cpuCount__
  def getMemoryUsage(self):
    return self.__totalMemKb, self.__actualMemKb, self.__buffersMemKb, self.__cachedMemKb
  def getLoadAvg(self):
    return  self.__loadavg__, self.__noofprocs__, self.__noofrunningprocs__, self.__lastpid__

