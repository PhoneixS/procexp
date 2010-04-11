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

class procreader(object):
  def __init__(self, timerValue, historyCount):
    self.__initReader__()
    self.__uidFilter__ = None
    self.__updateTimer__ = timerValue
    self.__historyCount__ = historyCount
 
  def __initReader__(self):
    self.__processList__ = {}
    self.__closedProcesses__ = None
    self.__newProcesses__ = None
    self.__prevJiffies__ = None
    self.__deltaJiffies__ = None

  def __getGlobalJiffies__(self):
    jiffyStr = procutils.readFullFile('/proc/stat').split("\n")[0]
    newjiffies = int(jiffyStr.split()[1]) + int(jiffyStr.split()[2]) + int(jiffyStr.split()[3]) + int(jiffyStr.split()[4]) 
    if self.__deltaJiffies__ == None:
      self.__prevJiffies__ = newjiffies
      self.__deltaJiffies__ = 1
    else:
      self.__deltaJiffies__ = newjiffies - self.__prevJiffies__
      self.__prevJiffies__ = newjiffies    
  
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
          
  def getProcessInfo(self):
    self.__getGlobalJiffies__()
    self.__getAllProcesses__()
    self.__getProcessCpuDetails__()
    self.__removeUnknownParents__()
    self.__getProcessDetails__()
    self.__getAllSocketInfo__()
    self.__getAllUDPInfo__()
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
