#!/usr/bin/python
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

#Thanks to the following developers helping:
#
#  Diaa Sami, making the GUI more usable
#



import procreader.reader
import ui.main
import logui
import aboutui 
import procutils
import os
import singleprocess
import systemoverview
import configobj
import settings as settingsMenu

import plotobjects
import networkoverview
import colorlegend
from PyQt4 import QtCore, QtGui

import cpuaffinity
import sys
import signal
import procreader.tcpip_stat as tcpip_stat
import rootproxy
import messageui




timer = None
reader = None
treeProcesses = {} #flat dictionary of processes
toplevelItems = {}
mainUi = None
onlyUser = True
greenTopLevelItems = {}
redTopLevelItems = {}
singleProcessUiList = {}
curveCpuHist = None
curveCpuSystemHist = None
curveIoWaitHist = None
curveIrqHist = None

curveCpuPlotGrid = None
cpuUsageHistory = None
cpuUsageSystemHistory = None
cpuUsageIoWaitHistory = None
cpuUsageIrqHistory = None
systemOverviewUi = None
networkOverviewUi = None
MainWindow = None

firstUpdate = True

procList = {}


#default settings
settings = {}
defaultSettings = \
{"fontSize": 10, 
 "columnWidths": [100,60,40,100,30,30,30,30],
 "updateTimer": 1000,
 "historySampleCount": 200
}

def performMenuAction(action):
  global procList
  global onlyUser
  global settings
  global systemOverviewUi
  global networkOverviewUi
  if action is mainUi.actionKill_process:
    try:
      selectedItem = mainUi.processTreeWidget.selectedItems()[0]
    except IndexError:
      return
    process = selectedItem.data(1,0).toString()
    procutils.killProcessHard(process)
  elif action is mainUi.actionKill_process_tree:
    try:
      selectedItem = mainUi.processTreeWidget.selectedItems()[0]
    except IndexError:
      return
    process = selectedItem.data(1,0).toString()
    killProcessTree(process, procList)
  elif action is mainUi.actionShow_process_from_all_users:
    if onlyUser:
      reader.noFilterUID()
      clearTree()
      onlyUser = False
    else:
      reader.setFilterUID(os.geteuid())
      clearTree()
      onlyUser = True
  elif action is mainUi.actionProperties:
    try:
      selectedItem = mainUi.processTreeWidget.selectedItems()[0]
    except IndexError:
      return
    process = str(selectedItem.data(1,0).toString())
    if singleProcessUiList.has_key(process):
      singleProcessUiList[process].makeVisible()
    else:
      if procList.has_key(int(process)):
        singleProcessUiList[process] = singleprocess.singleUi(process, procList[int(process)]["cmdline"], procList[int(process)]["name"], reader, int(settings["historySampleCount"]))
  elif action is mainUi.actionSaveSettings:
    saveSettings()
  elif action is mainUi.actionSettings:
    msec, depth, fontSize = settingsMenu.doSettings(int(settings["updateTimer"]),\
                                                       int(settings["historySampleCount"]), \
                                                       int(settings["fontSize"]))
    settings["updateTimer"] = int(msec)
    settings["historySampleCount"] = int(depth)
    settings["fontSize"] = int(fontSize)
    
    setFontSize(fontSize)
  elif action is mainUi.actionSystem_information:
    systemOverviewUi.show()
  elif action is mainUi.actionNetwork_Information:
    networkOverviewUi.show()
  elif action is mainUi.actionClose_all_and_exit:
    for window in singleProcessUiList:
      singleProcessUiList[window].closeWindow()
    systemOverviewUi.close()
    networkOverviewUi.close()
    MainWindow.close()
    if logui.dialog is not None:
      logui.dialog.close()
    if aboutui.dialog is not None:
      aboutui.dialog.close()
  elif action is mainUi.actionColor_legend:
    colorlegend.doColorHelpLegend()
  elif action is mainUi.actionSet_affinity:
    try:
      selectedItem = mainUi.processTreeWidget.selectedItems()[0]
      process = str(selectedItem.data(1,0).toString())
    except IndexError:
      return
    cpuaffinity.doAffinity(reader.getCpuCount(), process)
  elif action is mainUi.actionLog:
    logui.doLogWindow()
  elif action is mainUi.actionAbout:
    aboutui.doAboutWindow()
  elif action is mainUi.actionClear_Messages:
    messageui.clearAllMessages()
  else:
    procutils.log("This action (%s)is not yet supported." %action)

def setFontSize(fontSize):
  global settings
  settings["fontSize"] = fontSize
  font = QtGui.QFont()
  font.setPointSize(fontSize)
  mainUi.menuFile.setFont(font)
  mainUi.menuOptions.setFont(font)
  mainUi.menuView.setFont(font)
  mainUi.menuProcess.setFont(font)
  mainUi.menuSettings.setFont(font)
  mainUi.menubar.setFont(font)
  mainUi.processTreeWidget.setFont(font)
  if systemOverviewUi is not None:
    systemOverviewUi.setFontSize(fontSize)
  if networkOverviewUi is not None:
    networkOverviewUi.setFontSize(fontSize)
  
  
def loadSettings():
  global settings
  settingsPath = os.path.expanduser("~/.procexp/settings")
  if os.path.exists(settingsPath):
    f = file(settingsPath,"rb")
    settingsObj = configobj.ConfigObj(infile=f)
    settings=settingsObj.dict()
    
  #load default settings for undefined settings
  for item in defaultSettings:
    if settings.has_key(item):
      pass
    else:
      settings[item] = defaultSettings[item]
    
  fontsize = int(settings["fontSize"])
  setFontSize(fontsize)
  
  #set the columnwidths
  for headerSection in range(mainUi.processTreeWidget.header().count()):
    try:
      width = int(settings["columnWidths"][headerSection])
    except:
      width = 150
    mainUi.processTreeWidget.header().resizeSection(headerSection,width)
    
  #load default settings for undefined settings
  for item in defaultSettings:
    if settings.has_key(item):
      pass
    else:
      settings[item] = defaultSettings[item]
      
  global cpuUsageHistory
  global cpuUsageSystemHistory
  global cpuUsageIoWaitHistory
  global cpuUsageIrqHistory 
  
  cpuUsageHistory = [0] * int(settings["historySampleCount"])
  cpuUsageSystemHistory = [0] * int(settings["historySampleCount"])
  cpuUsageIoWaitHistory = [0] * int(settings["historySampleCount"])
  cpuUsageIrqHistory = [0] * int(settings["historySampleCount"])


def saveSettings():

  widths = []
  for headerSection in range(mainUi.processTreeWidget.header().count()):
    widths.append(mainUi.processTreeWidget.header().sectionSize(headerSection))
  settings["columnWidths"] = widths
  
  settingsPath = os.path.expanduser("~/.procexp")
  if not(os.path.exists(settingsPath)):
    os.makedirs(settingsPath)
  f = file(settingsPath + "/settings","wb")
  cfg = configobj.ConfigObj(settings)
  cfg.write(f)
  f.close()

def onContextMenu(point):
  global mainUi
  mainUi.menuProcess.exec_(mainUi.processTreeWidget.mapToGlobal(point))


treeViewcolumns = ["Process","PID","CPU","Command Line", "User", "Chan","#thread"]

def onHeaderContextMenu(point):
  menu = QtGui.QMenu()
  for idx, col in enumerate(treeViewcolumns):
    action = QtGui.QAction(col, mainUi.processTreeWidget)
    action.setCheckable(True)
    action.setChecked(not mainUi.processTreeWidget.isColumnHidden(idx))
    action.setData(idx)
    menu.addAction(action)
  selectedItem = menu.exec_(mainUi.processTreeWidget.mapToGlobal(point))
  if selectedItem is not None:
    mainUi.processTreeWidget.setColumnHidden(selectedItem.data().toInt()[0], not selectedItem.isChecked())
  
def prepareUI(mainUi):
  global timer
  
  mainUi.processTreeWidget.setColumnCount(len(treeViewcolumns))
  
  mainUi.processTreeWidget.setHeaderLabels(treeViewcolumns)
  mainUi.processTreeWidget.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
  mainUi.processTreeWidget.header().customContextMenuRequested.connect(onHeaderContextMenu)
  
  
  #create a timer
  timer = QtCore.QTimer(mainUi.processTreeWidget)
  QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), updateUI)
  QtCore.QObject.connect(mainUi.processTreeWidget, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), onContextMenu)
  QtCore.QObject.connect(mainUi.menuFile,  QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuProcess,  QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuOptions,  QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuSettings, QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuView, QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuHelp, QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  
  #prepare the plot
  global curveCpuHist
  global curveCpuSystemHist
  global curveIoWaitHist
  global curveIrqHist
  global curveCpuPlotGrid
  
  curveCpuHist = plotobjects.niceCurve("CPU History", 
                           1 , QtGui.QColor(0,255,0),QtGui.QColor(0,170,0), 
                           mainUi.qwtPlotOverallCpuHist)
  
  curveCpuSystemHist = plotobjects.niceCurve("CPU Kernel History", 
                           1, QtGui.QColor(255,0,0),QtGui.QColor(170,0,0), 
                           mainUi.qwtPlotOverallCpuHist)
                           
  curveIoWaitHist = plotobjects.niceCurve("CPU IO wait history", 
                           1, QtGui.QColor(0,0,255),QtGui.QColor(0,0,127), 
                           mainUi.qwtPlotOverallCpuHist)
  
  curveIrqHist = plotobjects.niceCurve("CPU irq history", 
                           1, QtGui.QColor(0,255,255),QtGui.QColor(0,127,127), 
                           mainUi.qwtPlotOverallCpuHist)

  scale = plotobjects.scaleObject()
  scale.min = 0
  scale.max = 100
  _ = plotobjects.procExpPlot(mainUi.qwtPlotOverallCpuHist, scale, hasGrid=False)
  
def clearTree():
  global mainUi
  global treeProcesses
  global toplevelItems
  global greenTopLevelItems
  global redTopLevelItems
  
  mainUi.processTreeWidget.clear()
  treeProcesses = {}
  toplevelItems = {}
  greenTopLevelItems = {}
  redTopLevelItems = {}
  
def killProcessTree(proc, procList):
  killChildsTree(int(str(proc)), procList)
  procutils.killProcessHard(int(str(proc)))

def killChildsTree(proc, procList):
  for aproc in procList:
    if procList[aproc]["PPID"] == proc:
      killChildsTree(aproc, procList)
      procutils.killProcess(aproc)
     
def addProcessAndParents(proc, procList):
  global mainUi
  
  if treeProcesses.has_key(proc):
    return treeProcesses[proc]
    
  treeProcesses[proc] = QtGui.QTreeWidgetItem([])
  greenTopLevelItems[proc] = treeProcesses[proc]
  
  if procList[proc]["PPID"] > 0 and procList.has_key(procList[proc]["PPID"]): #process has a parent
    parent = addProcessAndParents(procList[proc]["PPID"],procList)
    parent.addChild(treeProcesses[proc])
  else: #process has no parent, thus it is toplevel. add it to the treewidget
    mainUi.processTreeWidget.addTopLevelItem(treeProcesses[proc])    
    toplevelItems[proc] = treeProcesses[proc]
  
  return treeProcesses[proc]
  
def delChild(item, childtodelete):
  if item != None:
    for index in xrange(item.childCount()):
      thechild = item.child(index)
      if thechild != None:
        if thechild == childtodelete:
          item.takeChild(index)
        else:
          delChild(thechild, childtodelete)
          
def expandChilds(parent):
  global mainUi
  for index in xrange(parent.childCount()):
    thechild = parent.child(index)
    if thechild != None:
      mainUi.processTreeWidget.expandItem(thechild)
      expandChilds(thechild)
    else:
      mainUi.processTreeWidget.expandItem(parent)
      

def expandAll():
  global mainUi
  for topLevelIndex in xrange(mainUi.processTreeWidget.topLevelItemCount()):
    item = mainUi.processTreeWidget.topLevelItem(topLevelIndex)
    expandChilds(item)

def updateUI():
  """update"""
  tcpip_stat.tick()
  try:
    global procList
    global treeProcesses, greenTopLevelItems, redTopLevelItems
    global mainUi
    global firstUpdate
    
    if mainUi.freezeCheckBox.isChecked():
      return
    
    reader.doReadProcessInfo()
    procList, closedProc, newProc = reader.getProcessInfo()

    #color all green processes with default background
    defaultBgColor = app.palette().color(QtGui.QPalette.Base)  
    for proc in greenTopLevelItems:
      for column in xrange(greenTopLevelItems[proc].columnCount()):
        greenTopLevelItems[proc].setBackgroundColor(column, defaultBgColor)
    greenTopLevelItems = {}
   
    #delete all red widgetItems
    for proc in redTopLevelItems:
      for topLevelIndex in xrange(mainUi.processTreeWidget.topLevelItemCount()):
        topLevelItem = mainUi.processTreeWidget.topLevelItem(topLevelIndex)
        delChild(topLevelItem, redTopLevelItems[proc])
        if topLevelItem == redTopLevelItems[proc]:
          mainUi.processTreeWidget.takeTopLevelItem(topLevelIndex)
          
    redTopLevelItems = {}
    
    #create new items and mark items to be deleted red
    #draw tree hierarchy of processes
    for proc in newProc:
      widgetItem = addProcessAndParents(proc, procList)


    #if the process has childs which do still exist, "reparent" the child.
    for proc in procList:
      if procList[proc]["PPID"] == 0:
        item = treeProcesses[proc]
        if item.parent() is not None:
          parentItem = item.parent()
          for idx in xrange(parentItem.childCount()):
            if item == parentItem.child(idx):
              parentItem.takeChild(idx)
          mainUi.processTreeWidget.addTopLevelItem(treeProcesses[proc])

    #copy processed to be deleted to the red list      
    for proc in closedProc:
      try:
        redTopLevelItems[proc] = treeProcesses[proc]
      except KeyError:
        pass
     
        
    #color all deleted processed red 
    for proc in redTopLevelItems:
      try:
        for column in xrange(redTopLevelItems[proc].columnCount()):
          redTopLevelItems[proc].setBackgroundColor(column, QtGui.QColor(255,0,0))
      except RuntimeError:
        pass 
    
    #update status information about the processes  
    try:
      for proc in procList:   
        treeProcesses[proc].setData(0, 0, procList[proc]["name"])
        treeProcesses[proc].setData(1, 0, str(proc))
        treeProcesses[proc].setData(2, 0, procList[proc]["cpuUsage"])
        treeProcesses[proc].setData(3, 0, procList[proc]["cmdline"])
        treeProcesses[proc].setData(4, 0, procList[proc]["uid"])
        treeProcesses[proc].setData(5, 0, procList[proc]["wchan"])
        treeProcesses[proc].setData(6, 0, procList[proc]["nfThreads"])
    except RuntimeError:
      #underlying c++ object has been deleted
      pass

    for proc in closedProc:
      try:
        del treeProcesses[proc]
      except KeyError:
        pass

    #color all new processes 'green'
    if firstUpdate == False:
      for proc in greenTopLevelItems:
        item = greenTopLevelItems[proc]
        for column in xrange(item.columnCount()):
          item.setBackgroundColor(column, QtGui.QColor(0,255,0))
      
    if (len(closedProc) > 0) or (len(newProc) > 0):
      expandAll()
    
    for ui in singleProcessUiList:
      singleProcessUiList[ui].update()
      
    #update CPU plots
    systemOverviewUi.update()
    
    #network plots
    networkOverviewUi.update()
      
    #update the cpu graph
    global cpuUsageHistory
    global cpuUsageSystemHistory
    global cpuUsageIoWaitHistory
    global cpuUsageIrqHistory
    
    global curveCpuHist
    global curveCpuSystemHist
    global curveIrqHist
    global curveIoWaitHist
    global curveCpuPlotGrid
    
    cpuUsageHistory.append(reader.overallUserCpuUsage()+
                           reader.overallSystemCpuUsage()+
                           reader.overallIoWaitCpuUsage()+
                           reader.overallIrqCpuUsage())
    cpuUsageHistory = cpuUsageHistory[1:]
    
    
    cpuUsageSystemHistory.append(reader.overallSystemCpuUsage()+
                                 reader.overallIoWaitCpuUsage()+
                                 reader.overallIrqCpuUsage())
    cpuUsageSystemHistory = cpuUsageSystemHistory[1:]
    
    
    cpuUsageIoWaitHistory.append(reader.overallIoWaitCpuUsage() + 
                                 reader.overallIrqCpuUsage())
    cpuUsageIoWaitHistory = cpuUsageIoWaitHistory[1:]
    
    
    cpuUsageIrqHistory.append(reader.overallIrqCpuUsage())
    cpuUsageIrqHistory = cpuUsageIrqHistory[1:]
    


                                 
    curveCpuHist.setData(range(int(settings["historySampleCount"])), cpuUsageHistory)
    curveCpuSystemHist.setData(range(int(settings["historySampleCount"])), cpuUsageSystemHistory)
    curveIoWaitHist.setData(range(int(settings["historySampleCount"])), cpuUsageIoWaitHistory)
    curveIrqHist.setData(range(int(settings["historySampleCount"])), cpuUsageIrqHistory)
    mainUi.qwtPlotOverallCpuHist.replot()

    logui.update()

    #update memory figures
    mem = reader.getMemoryUsage()
    totalSwap = mem[5]
    actualSwap = mem[4]
    mainUi.memory.setValue(mem[0]-mem[1])
    mainUi.memory.setMaximum(mem[0])
    mainUi.swap.setValue(actualSwap)
    if totalSwap > 0:
      mainUi.swap.setMaximum(totalSwap)
    else:
      mainUi.swap.setMaximum(1)

  except:
    import traceback
    procutils.log("Unhandled exception:%s" %traceback.format_exc())
    print traceback.format_exc()
  
  firstUpdate = False



app = QtGui.QApplication(sys.argv)
MainWindow = QtGui.QMainWindow()
mainUi = ui.main.Ui_MainWindow()
mainUi.setupUi(MainWindow)

prepareUI(mainUi)
loadSettings()


MainWindow.show()
app.processEvents()

rootproxy.start(asRoot=True)
if not rootproxy.isStarted():
  messageui.doMessageWindow("Process explorer has no root privileges. TCPIP traffic monitoring (using tcpdump) will not be available.")

reader = procreader.reader.procreader(int(settings["updateTimer"]), int(settings["historySampleCount"]))

timer.start(int(settings["updateTimer"]))

if onlyUser:
  reader.setFilterUID(os.geteuid())

systemOverviewUi = systemoverview.systemOverviewUi(reader.getCpuCount(), int(settings["historySampleCount"]), reader)
networkOverviewUi = networkoverview.networkOverviewUi(reader.getNetworkCards(), int(settings["historySampleCount"]), reader)

systemOverviewUi.setFontSize(int(settings["fontSize"]))
networkOverviewUi.setFontSize(int(settings["fontSize"]))

updateUI()

signal.signal(signal.SIGINT, signal.SIG_DFL)

app.exec_()
tcpip_stat.stop()
rootproxy.end()
sys.exit()

