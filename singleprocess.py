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


#
# Display process properties and statistics of a single process
#
import procutils
import os
import ui.processdetails
import datetime
from PyQt4 import QtCore, QtGui
import PyQt4.Qwt5 as Qwt
import subprocess

import procreader.tcpip_stat as tcpip_stat

import copy
UNKNOWN = "---" 

tcpstates = [\
"UNUSED",\
"TCP_ESTABLISHED",\
"TCP_SYN_SENT",\
"TCP_SYN_RECV",\
"TCP_FIN_WAIT1",\
"TCP_FIN_WAIT2",\
"TCP_TIME_WAIT",\
"TCP_CLOSE",\
"TCP_CLOSE_WAIT",\
"TCP_LAST_ACK",\
"TCP_LISTEN",\
"TCP_CLOSING"]

class singleProcessDetailsAndHistory(object):
  def __init__(self, pid, historyDepth, prefixDir = ""):
    self._prefixDir = prefixDir
    self.__pid__ = str(pid)
    self.__pathPrefix__ = self._prefixDir+"/proc/"+self.__pid__+"/"
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
    self.threads = {}

  def __getOpenFileNames__(self):
    alldirs = os.listdir(self.__pathPrefix__ + "fd")
    self.__openFiles__ = {}
    for thedir in alldirs:
      self.__openFiles__[thedir] = {"path":os.readlink(self.__pathPrefix__ + dir)}
  
  def _getThreadsInfo__(self):
    alldirs = os.listdir(self.__pathPrefix__ + "task/")
    self.threads = {}
    for t in alldirs:
      try:
        wchan = procutils.readFullFile(self.__pathPrefix__ + "task/" + str(t) + "/wchan")
        sched = procutils.readFullFile(self.__pathPrefix__ + "task/" + str(t) + "/sched")
        wakeupcount = int(sched.split("\n")[23].split(":")[1]) #23 is wakeupcount 
        self.threads[t] = [wchan, "wakeups %s" %wakeupcount]
      except:
        pass
    
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
        self.cmdline = procutils.readFullFile(self.__pathPrefix__ + "cmdline").replace("\x00"," ")
      except OSError, val:
        self.cmdline = "<"+val.strerror+">"
      except procutils.FileError:
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
        procstartedtime_seconds = procutils.readFullFile(self.__pathPrefix__ + "stat").split(" ")[21]
      
      
        procstat = procutils.readFullFile(self._prefixDir+"/proc/stat").split("\n")
        for line in procstat:
          if line.find("btime") != -1:
            systemstarted_seconds = line.split(" ")[1]
        HZ = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        epoch = datetime.datetime(month=1,day=1,year=1970)
        
        
        procstarted = epoch + \
                      datetime.timedelta(seconds=int(systemstarted_seconds)) + \
                      datetime.timedelta(seconds=int(int(procstartedtime_seconds)/(HZ*1.0)+0.5))
        
        self.startedtime = procstarted.strftime("%A, %d. %B %Y %I:%M%p")
      except procutils.FileError:
        self.startedtime = "--"
      
    #process parent pid
    if self.ppid is None:
      try:
        self.ppid = procutils.readFullFile(self.__pathPrefix__ + "stat").split(" ")[3]
      except procutils.FileError:
        self.ppid = None
        
    #all threads
    self._getThreadsInfo__()
      
      
class singleUi(object):
  def __init__(self, proc, cmdLine, name, reader, depth):
    self.__depth__ = depth
    self.__proc__ = proc
    self.__reader__ = reader
    self.__name__ = name
    self.__dialog__ = QtGui.QDialog()
    self.__procDetails__ = ui.processdetails.Ui_Dialog()
    self.__procDetails__.setupUi(self.__dialog__)
    self.__dialog__.show()
    self.__dialog__.setWindowTitle(proc+":"+cmdLine+" Properties")
    self.__processGone__ = False
    self.__y__ = range(self.__depth__)
    self.__tcpConnections__ = []
    self.__tcpStat__ = None
    self.__TCPHist__ = [0] * self.__reader__.getHistoryDepth(self.__proc__)
    self.__prevtcpipbytes__ = 0

    #-------- top plot CPU usage-------------------------------------------------------------------
    #Curves for CPU usage
    self.__curveCpuHist__ = Qwt.QwtPlotCurve("CPU History")
    pen = QtGui.QPen(QtGui.QColor(0,255,0))
    pen.setWidth(2)
    
    #work around to get better plotting.
    self.__curveCpuHistExt__ = Qwt.QwtPlotCurve("CPU History extra")
    self.__curveCpuHistExt__.setPen(QtGui.QPen(QtGui.QColor(0,255,0)))
    self.__curveCpuHistExt__.attach(self.__procDetails__.qwtPlotCpuHist)
    
    
    self.__curveCpuHist__.setPen(pen)
    self.__curveCpuHist__.setBrush(QtGui.QColor(0,170,0))
    self.__curveCpuHist__.attach(self.__procDetails__.qwtPlotCpuHist)
    
    #Curve for kernel usage
    self.__curveCpuKernelHist__ = Qwt.QwtPlotCurve("CPU Kernel History")
    pen = QtGui.QPen(QtGui.QColor(255,0,0))
    pen.setWidth(1)
    self.__curveCpuKernelHist__.setPen(pen)
    self.__curveCpuKernelHist__.setBrush(QtGui.QColor(170,0,0))
    self.__curveCpuKernelHist__.attach(self.__procDetails__.qwtPlotCpuHist)
    
    #work around to get better plotting.
    self.__curveCpuKernelHistExt__ = Qwt.QwtPlotCurve("CPU Kernel History extra")
    self.__curveCpuKernelHistExt__.setPen(QtGui.QPen(QtGui.QColor(255,0,0)))
    self.__curveCpuKernelHistExt__.attach(self.__procDetails__.qwtPlotCpuHist)
    
    
    #self.__procDetails__.qwtPlotCpuHist.setAxisScale(0,0,self.__depth__,10)    
    
    self.__curveCpuPlotGrid__ = Qwt.QwtPlotGrid()
    self.__curveCpuPlotGrid__.setMajPen(QtGui.QPen(QtGui.QColor(0,100,0), 0, QtCore.Qt.SolidLine))
    self.__curveCpuPlotGrid__.setMinPen(QtGui.QPen(QtGui.QColor(0,100,0), 0, QtCore.Qt.SolidLine))
    self.__curveCpuPlotGrid__.enableXMin(True)
    self.__curveCpuPlotGrid__.attach(self.__procDetails__.qwtPlotCpuHist)
    #----------------------------------------------------------------------------------------------
    
    
    #-------- Middle plot memory usage-------------------------------------------------------------
    #Curve for memory usage
    self.__curveRssHist__ = Qwt.QwtPlotCurve("Rss History")
    pen = QtGui.QPen(QtGui.QColor(248,248,0))
    pen.setWidth(1)
    self.__curveRssHist__.setPen(pen)
    self.__curveRssHist__.setBrush(QtGui.QColor(190,190,0))
    self.__curveRssHist__.attach(self.__procDetails__.qwtPlotRssHist)
    
    self.__curveRssHistExt__ = Qwt.QwtPlotCurve("Rss extra")
    self.__curveRssHistExt__.setPen(QtGui.QPen(QtGui.QColor(248,248,0)))
    self.__curveRssHistExt__.attach(self.__procDetails__.qwtPlotRssHist)
    
    #self.__procDetails__.qwtPlotRssHgetThreist.setAxisScale(0,0,100,10)
    self.__RssPlotGrid__ = Qwt.QwtPlotGrid()
    self.__RssPlotGrid__.setMajPen(QtGui.QPen(QtGui.QColor(0,100,0), 0, QtCore.Qt.SolidLine))
    self.__RssPlotGrid__.setMinPen(QtGui.QPen(QtGui.QColor(0,100,0), 0, QtCore.Qt.SolidLine))
    self.__RssPlotGrid__.enableXMin(True)
    self.__RssPlotGrid__.attach(self.__procDetails__.qwtPlotRssHist)
    #----------------------------------------------------------------------------------------------
    
    #-------- Bottom plot IO usage ----------------------------------------------------------------
    #Curve for memory usage
    self.__curveIOHist__ = Qwt.QwtPlotCurve("IO History")
    pen = QtGui.QPen(QtGui.QColor(0,214,214))
    pen.setWidth(1)
    self.__curveIOHist__.setPen(pen)
    self.__curveIOHist__.setBrush(QtGui.QColor(0,150,150))
    self.__curveIOHist__.attach(self.__procDetails__.qwtPlotIoHist)
    
    self.__curveIOHistExt__ = Qwt.QwtPlotCurve("IO History extra")
    self.__curveIOHistExt__.setPen(QtGui.QPen(QtGui.QColor(0,214,214)))
    self.__curveIOHistExt__.attach(self.__procDetails__.qwtPlotIoHist)
    
    #self.__procDetails__.qwtPlotIoHist.setAxisScale(0,0,100,10)
    self.__IOPlotGrid__ = Qwt.QwtPlotGrid()
    self.__IOPlotGrid__.setMajPen(QtGui.QPen(QtGui.QColor(0,100,0), 0, QtCore.Qt.SolidLine))
    self.__IOPlotGrid__.setMinPen(QtGui.QPen(QtGui.QColor(0,100,0), 0, QtCore.Qt.SolidLine))
    self.__IOPlotGrid__.enableXMin(True)
    self.__IOPlotGrid__.attach(self.__procDetails__.qwtPlotIoHist)
    #----------------------------------------------------------------------------------------------

    #-------- TCP IO usage ----------------------------------------------------------------
    self.__curveTcpipHist__ = Qwt.QwtPlotCurve("TCPIP History")
    pen = QtGui.QPen(QtGui.QColor(0,214,214))
    pen.setWidth(1)
    self.__curveTcpipHist__.setPen(pen)
    self.__curveTcpipHist__.setBrush(QtGui.QColor(196,60,210))
    self.__curveTcpipHist__.attach(self.__procDetails__.qwtPlotTcpipHist)
    
    self.__curveTcpipHistExt__ = Qwt.QwtPlotCurve("TCPIP History extra")
    self.__curveTcpipHistExt__.setPen(QtGui.QPen(QtGui.QColor(215,124,224)))
    self.__curveTcpipHistExt__.attach(self.__procDetails__.qwtPlotTcpipHist)
    
    
    #self.__procDetails__.qwtPlotIoHist.setAxisScale(0,0,100,10)
    self.__TcpipPlotGrid__ = Qwt.QwtPlotGrid()
    self.__TcpipPlotGrid__.setMajPen(QtGui.QPen(QtGui.QColor(0,100,0), 0, QtCore.Qt.SolidLine))
    self.__TcpipPlotGrid__.setMinPen(QtGui.QPen(QtGui.QColor(0,100,0), 0, QtCore.Qt.SolidLine))
    self.__TcpipPlotGrid__.enableXMin(True)
    self.__TcpipPlotGrid__.attach(self.__procDetails__.qwtPlotTcpipHist)
    #----------------------------------------------------------------------------------------------
    
    #  all plots ----------------------------------------------------------------------------------
    self.__procDetails__.qwtPlotCpuHist.setCanvasBackground(QtGui.QColor(0,0,0))
    self.__procDetails__.qwtPlotRssHist.setCanvasBackground(QtGui.QColor(0,0,0))
    self.__procDetails__.qwtPlotIoHist.setCanvasBackground(QtGui.QColor(0,0,0))
    self.__procDetails__.qwtPlotTcpipHist.setCanvasBackground(QtGui.QColor(0,0,0))
    self.__procDetails__.qwtPlotCpuHist.enableAxis(0, False )
    self.__procDetails__.qwtPlotCpuHist.enableAxis(2, False )
    self.__procDetails__.qwtPlotRssHist.enableAxis(0, False )
    self.__procDetails__.qwtPlotRssHist.enableAxis(2, False )
    self.__procDetails__.qwtPlotIoHist.enableAxis(0, False )
    self.__procDetails__.qwtPlotIoHist.enableAxis(2, False )
    self.__procDetails__.qwtPlotTcpipHist.enableAxis(0, False )    
    self.__procDetails__.qwtPlotTcpipHist.enableAxis(2, False )
    #----------------------------------------------------------------------------------------------
    
    QtCore.QObject.connect(self.__procDetails__.pushButtonOK, QtCore.SIGNAL('clicked()'), self.__onClose__)
  
    # Fill some field only at construction time
    data = self.__reader__.getEnvironment(self.__proc__)
    text = ""
    for line in data:
      text = text + line + "\n"
    self.__procDetails__.environmentText.setPlainText(text)
    QtCore.QObject.connect(self.__procDetails__.filterEdit, QtCore.SIGNAL('textEdited(QString)'), self.__onFilterTextEdit__)
    
    self.update_sockets()
    self.__lddoutput__ = None
  def __del__(self):
    try:
      if self.__tcpStat__ != None:
        self.__tcpStat__.doStop()
        self.__tcpStat__.join()
    except OSError:
      pass
    
  def __onFilterTextEdit__(self):
    filter = str(self.__procDetails__.filterEdit.text())
    data = self.__reader__.getEnvironment(self.__proc__)
    text = ""
    for line in data:
      if line.upper().find(filter.upper()) != -1:
        text = text + line + "\n"
    self.__procDetails__.environmentText.setText(text)
    
  def __onClose__(self):
    self.__dialog__.setVisible(False)
  def makeVisible(self):
    self.__dialog__.setVisible(True)
    
  def closeWindow(self):
    self.__dialog__.close()
    
  def update_sockets(self):
    #fill tcp/ip values
    connections, udp = self.__reader__.getAllProcessSockets(self.__proc__)
    text = ""
    allConn = []
    for conn in connections:
      ipfrom = connections[conn][1].split(":")
      ipfromport = ipfrom[1]
      ipfromaddr = ipfrom[0]
      ipfromaddrdec = str(int(ipfromaddr[6:8],16)) + "." + str(int(ipfromaddr[4:6],16)) + "." + str(int(ipfromaddr[2:4],16)) + "." + str(int(ipfromaddr[0:2],16))
      
      
      
      ipto = connections[conn][2].split(":")
      iptoport = ipto[1]
      iptoaddr = ipto[0]

      iptoaddrdec   = str(int(iptoaddr[6:8],16)) + "." + str(int(iptoaddr[4:6],16)) + "." + str(int(iptoaddr[2:4],16)) + "." + str(int(iptoaddr[0:2],16))
      
      allConn.append(((ipfromaddrdec,int(ipfromport,16)),(iptoaddrdec,int(iptoport,16))))
      
      state = tcpstates[int(connections[conn][3],16)]
    
      text = text + "TCPIP  " + ipfromaddrdec +":"+ str(int(ipfromport,16))  + "<-->" + iptoaddrdec + ":"+ str(int(iptoport,16)) +" "+state + "\n"
      
    #create a tcpdump for tcp performance measurement of this process
    #in this object, only do stat if user requested the UI, because there will
    #be many tcpdumps running which is unacceptable.
    if self.__tcpConnections__ != allConn:
      self.__tcpConnections__ = copy.deepcopy(allConn)
      if self.__tcpStat__ != None:
        self.__tcpStat__.doStop()
        self.__tcpStat__.join()
      
      self.__tcpStat__ = tcpip_stat.tcpipstat(self.__tcpConnections__)
      self.__tcpStat__.start()
        
    if self.__tcpStat__ != None:
      nfBytes = self.__tcpStat__.nfBytes 
      if nfBytes - self.__prevtcpipbytes__ > 0:
        self.__TCPHist__.append(nfBytes - self.__prevtcpipbytes__)
      else:
        self.__TCPHist__.append(0)
      self.__prevtcpipbytes__ = nfBytes
    self.__TCPHist__ = self.__TCPHist__[1:]
    for conn in udp:
      ipfrom = udp[conn][1].split(":")
      ipfromport = ipfrom[1]
      ipfromaddr = ipfrom[0]
      ipfromaddrdec = str(int(ipfromaddr[6:8],16)) + "." + str(int(ipfromaddr[4:6],16)) + "." + str(int(ipfromaddr[2:4],16)) + "." + str(int(ipfromaddr[0:2],16))
      text = text + "  UDP  " + ipfromaddrdec +":"+ str(int(ipfromport,16))+"\n"
    self.__procDetails__.tcpipText.setText(text)
    
  def update(self):
    if self.__processGone__ == False:
      if not(self.__reader__.hasProcess(self.__proc__)):
        self.__processGone__ = True
        self.__dialog__.setWindowTitle(self.__name__+":"+self.__proc__+" Properties: dead")
        if self.__tcpStat__ != None:
          self.__tcpStat__.doStop()
          self.__tcpStat__.join()
        
      else:
        data = self.__reader__.getProcessCpuUsageHistory(self.__proc__)
        actual = data[-1:][0]
        self.__curveCpuHist__.setData(self.__y__, data)
        self.__curveCpuHistExt__.setData(self.__y__, data)
        
        
        data = self.__reader__.getProcessCpuUsageKernelHistory(self.__proc__)
        self.__curveCpuKernelHist__.setData(self.__y__, data)
        self.__curveCpuKernelHistExt__.setData(self.__y__, data)


        self.__procDetails__.qwtPlotCpuHist.replot()
        self.__procDetails__.labelActualCpuUsage.setText(str(actual) + "%")
        self.__procDetails__.actualCpu.setValue(actual)
        
        data = self.__reader__.getProcessRssUsageHistory(self.__proc__)
        actual = data[-1:][0]
        self.__curveRssHist__.setData(self.__y__, data)
        self.__curveRssHistExt__.setData(self.__y__, data)
        self.__procDetails__.qwtPlotRssHist.replot()
        self.__procDetails__.labelActualRss.setText(str(actual) + " kB")
        self.__procDetails__.actualRss.setValue(actual)
        
        data = self.__reader__.getIOHistory(self.__proc__)
        actual = data[-1:][0]
        self.__curveIOHist__.setData(self.__y__, data)
        self.__curveIOHistExt__.setData(self.__y__, data)
        self.__procDetails__.qwtPlotIoHist.replot()
        self.__procDetails__.labelActualIo.setText(str(actual) + " kB/s")
        self.__procDetails__.actualIo.setValue(actual)
        
        self.update_sockets()
        data = self.__TCPHist__
        try:
          actual = self.__TCPHist__[-1:][0] / 1024
        except IndexError:
          actual = 0
        self.__curveTcpipHist__.setData(self.__y__, data)
        self.__curveTcpipHistExt__.setData(self.__y__, data)
        self.__procDetails__.qwtPlotTcpipHist.replot()
        self.__procDetails__.labelActualTcpip.setText(str(actual) + " kB/s")
        self.__procDetails__.actualTcpip.setValue(actual)
        
        self.__procDetails__.imagePwdEdit.setText(self.__reader__.getcwd(self.__proc__))
        self.__procDetails__.imageCommandLineEdit.setText(self.__reader__.getcmdline(self.__proc__))
        self.__procDetails__.imagePathEdit.setText(self.__reader__.getexe(self.__proc__))
        
        self.__procDetails__.imagePidLabel.setText(str(self.__proc__))
        self.__procDetails__.imageStartedLabel.setText(self.__reader__.getstartedtime(self.__proc__))
        self.__procDetails__.imagePPidLabel.setText(self.__reader__.getppid(self.__proc__))
        
        #update ldd output. Do this here: then it happens only when the user wants to see it
        #by opening a process properties window
        
        
        if self.__lddoutput__ is None:
          try:
            exepath = self.__reader__.getexe(self.__proc__)
            ldd = subprocess.Popen(["ldd" , exepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = ldd.communicate()
            err = output[1]
            if len(err) >0:
              self.__lddoutput__ = err
            else:
              self.__lddoutput__ = output[0]
              self.__lddoutput__ = self.__lddoutput__.replace("\t","")
            self.__procDetails__.libraryTextEdit.setText(self.__lddoutput__)
            
          except:
            self.__lddoutput__  = "--"
        
        #thread ID's
        
        text = ""
        threadsInfo = self.__reader__.getThreads(self.__proc__)
        for t in threadsInfo:
          text += str(t)+" "+ str(threadsInfo[t]) + "\n"
        self.__procDetails__.threadTextEdit.setText(text)
   
