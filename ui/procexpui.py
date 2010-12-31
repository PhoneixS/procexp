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

import ui.main
import utils
import os
import singleprocessui
import systemoverviewui
import configobj
import settingsui
import plotobjects
import networkoverview
import colorlegend
from PyQt4 import QtCore, QtGui
import PyQt4.Qwt5 as Qwt
import cpuaffinityui
import sys
import copy
import threading
import time
  
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
app = None
curveCpuPlotGrid = None
cpuUsageHistory = None
cpuUsageSystemHistory = None
cpuUsageIoWaitHistory = None
cpuUsageIrqHistory = None
systemOverviewUiWindow = None
networkOverviewUi = None
MainWindow = None

firstUpdate = True

procList = {}
oldProcList = {}
#default settings
settings = {}

def performMenuAction(action):
  """actions of the menu's"""
  global onlyUser #pylint: disable-msg=W0603
  if action is mainUi.actionKill_process:
    selectedItem = mainUi.processTreeWidget.selectedItems()[0]
    process = selectedItem.data(1, 0).toString()
    utils.killProcessHard(process)
  elif action is mainUi.actionKill_process_tree:
    selectedItem = mainUi.processTreeWidget.selectedItems()[0]
    process = selectedItem.data(1, 0).toString()
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
    selectedItem = mainUi.processTreeWidget.selectedItems()[0]
    process = str(selectedItem.data(1, 0).toString())
    if singleProcessUiList.has_key(process):
      singleProcessUiList[process].makeVisible()
    else:
      singleProcessUiList[process] = singleprocessui.singleUi(process, 
                                                            procList[int(process)]["cmdline"], 
                                                            procList[int(process)]["name"], 
                                                            reader) 
      #int(settings["historySampleCount"]))
  elif action is mainUi.actionSaveSettings:
    saveSettings()
  elif action is mainUi.actionSettings:
    msec, depth, fontSize = settingsui.doSettings(int(settings["updateTimer"]), \
                                                       int(settings["historySampleCount"]), \
                                                       int(settings["fontSize"]))
    settings["updateTimer"] = int(msec)
    settings["historySampleCount"] = int(depth)
    settings["fontSize"] = int(fontSize)
    
    setFontSize(fontSize)
  elif action is mainUi.actionSystem_information:
    systemOverviewUiWindow.show()
  elif action is mainUi.actionNetwork_Information:
    networkOverviewUi.show()
  elif action is mainUi.actionClose_this_window:
    MainWindow.close()
  elif action is mainUi.actionClose_all_and_exit:
    for window in singleProcessUiList:
      singleProcessUiList[window].closeWindow()
    MainWindow.close()
  elif action is mainUi.actionColor_legend:
    colorlegend.doColorHelpLegend()
  elif action is mainUi.actionSet_affinity:
    cpuaffinityui.doAffinity()
  else:
    print action, "This action is not yet supported."

def setFontSize(fontSize):
  """set the font size of all GUI's """
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
  if systemOverviewUiWindow is not None:
    systemOverviewUiWindow.setFontSize(fontSize)
  if networkOverviewUi is not None:
    networkOverviewUi.setFontSize(fontSize)
  
def saveSettings():
  """save settings """
  widths = []
  for headerSection in range(mainUi.processTreeWidget.header().count()):
    widths.append(mainUi.processTreeWidget.header().sectionSize(headerSection))
  settings["columnWidths"] = widths
  
  settingsPath = os.path.expanduser("~/.procexp")
  if not(os.path.exists(settingsPath)):
    os.makedirs(settingsPath)
  f = file(settingsPath + "/settings", "wb")
  cfg = configobj.ConfigObj(settings)
  cfg.write(f)
  f.close()

def onContextMenu(point):
  """onContextMenu"""
  mainUi.menuProcess.exec_(mainUi.processTreeWidget.mapToGlobal(point))


treeViewcolumns = ["Process", "PID", "CPU", "Command Line",  "User",  "Chan", "#thread"]
 
def onHeaderContextMenu(point):
  """onHeaderContextMenu"""
  menu = QtGui.QMenu()
  for idx, col in enumerate(treeViewcolumns):
    action = QtGui.QAction(col, mainUi.processTreeWidget)
    action.setCheckable(True)
    action.setChecked(not mainUi.processTreeWidget.isColumnHidden(idx))
    action.setData(idx)
    menu.addAction(action)
  selectedItem = menu.exec_(mainUi.processTreeWidget.mapToGlobal(point))
  mainUi.processTreeWidget.setColumnHidden(selectedItem.data().toInt()[0], 
                                           not selectedItem.isChecked())


class Signaller(QtCore.QThread):
  """an instance This class signals the GUI to update"""
  def __init__(self):
    QtCore.QThread.__init__(self, None)
    self.stop = False
    self.event = threading.Event()
    self.emit(QtCore.SIGNAL("updateUI()"))
  def doSignal(self):
    """give the UI update signal"""
    self.event.set()
  def run(self):
    """Translate the events into QtGui signals"""
    while self.stop == False:
      self.event.wait(0.5)
      if self.event.isSet():
        self.event.clear()
        self.emit(QtCore.SIGNAL("updateUI()"))

g_signaller = None

  
def prepareUI():
  """prepare the UI"""
  mainUi.processTreeWidget.setColumnCount(len(treeViewcolumns))
  
  mainUi.processTreeWidget.setHeaderLabels(treeViewcolumns)
  mainUi.processTreeWidget.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
  mainUi.processTreeWidget.header().customContextMenuRequested.connect(onHeaderContextMenu)
  
  global g_signaller #pylint: disable-msg=W0603
  g_signaller = Signaller()
  g_signaller.start()
  
  QtCore.QObject.connect(g_signaller, QtCore.SIGNAL("updateUI()"), updateUI)
  QtCore.QObject.connect(mainUi.processTreeWidget, 
                         QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), onContextMenu)
  QtCore.QObject.connect(mainUi.menuFile,  
                         QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuProcess,  
                         QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuOptions,  
                         QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuSettings, 
                         QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuView, 
                         QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuHelp, 
                         QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  
  #prepare the plot
  global curveCpuHist #pylint: disable-msg=W0603
  global curveCpuSystemHist #pylint: disable-msg=W0603
  global curveIoWaitHist #pylint: disable-msg=W0603
  global curveIrqHist #pylint: disable-msg=W0603
  
  curveCpuHist = plotobjects.niceCurve("CPU History", 
                           1 , QtGui.QColor(0, 255, 0), QtGui.QColor(0, 170, 0), 
                           mainUi.qwtPlotOverallCpuHist)
  
  curveCpuSystemHist = plotobjects.niceCurve("CPU Kernel History", 
                           1, QtGui.QColor(255, 0, 0), QtGui.QColor(170, 0, 0), 
                           mainUi.qwtPlotOverallCpuHist)
                           
  curveIoWaitHist = plotobjects.niceCurve("CPU IO wait history", 
                           1, QtGui.QColor(0, 0, 255), QtGui.QColor(0, 0, 127), 
                           mainUi.qwtPlotOverallCpuHist)
  
  curveIrqHist = plotobjects.niceCurve("CPU irq history", 
                           1, QtGui.QColor(0, 255, 255), QtGui.QColor(0, 127, 127), 
                           mainUi.qwtPlotOverallCpuHist)

  scale = plotobjects.scaleObject()
  scale.min = 0
  scale.max = 100
  plot = plotobjects.procExpPlot(mainUi.qwtPlotOverallCpuHist, scale)
  
def clearTree():
  """clear the process tree"""
  mainUi.processTreeWidget.clear()
  treeProcesses.clear()
  toplevelItems.clear()
  greenTopLevelItems.clear()
  redTopLevelItems.clear()
  
def killProcessTree(proc, theProcList):
  """kill all processes which are child of proc, and kill proc also"""
  killChildsTree(int(str(proc)), theProcList)
  utils.killProcessHard(int(str(proc)))

def killChildsTree(proc, theProcList):
  """kill all processes which are child of proc"""
  for aproc in theProcList:
    if theProcList[aproc]["PPID"] == proc:
      killChildsTree(aproc, theProcList)
      utils.killProcess(aproc)
     
def addProcessAndParents(proc, theProcList):
  """add process and all its parents to the tree"""
  if treeProcesses.has_key(proc):
    return treeProcesses[proc]
    
  treeProcesses[proc] = QtGui.QTreeWidgetItem([])
  greenTopLevelItems[proc] = treeProcesses[proc]
  
  if theProcList[proc]["PPID"] > 0 and theProcList.has_key(theProcList[proc]["PPID"]): #has a parent
    parent = addProcessAndParents(theProcList[proc]["PPID"], theProcList)
    parent.addChild(treeProcesses[proc])
  else: #process has no parent, thus it is toplevel. add it to the treewidget
    mainUi.processTreeWidget.addTopLevelItem(treeProcesses[proc])    
    toplevelItems[proc] = treeProcesses[proc]
  
  return treeProcesses[proc]
  
def delChild(item, childtodelete):
  """delete a child"""
  if item != None:
    for index in xrange(item.childCount()):
      thechild = item.child(index)
      if thechild != None:
        if thechild == childtodelete:
          item.takeChild(index)
        else:
          delChild(thechild, childtodelete)
          
def expandChilds(parent):
  """expand all childs"""
  for index in xrange(parent.childCount()):
    thechild = parent.child(index)
    if thechild != None:
      mainUi.processTreeWidget.expandItem(thechild)
      expandChilds(thechild)
    else:
      mainUi.processTreeWidget.expandItem(parent)

def expandAll():
  """expand all in tree"""
  for topLevelIndex in xrange(mainUi.processTreeWidget.topLevelItemCount()):
    item = mainUi.processTreeWidget.topLevelItem(topLevelIndex)
    expandChilds(item)

def updateUI(): #pylint: disable-msg=R0912
  """update the UI"""
  global firstUpdate #pylint: disable-msg=W0603
  global procList #pylint: disable-msg=W0603
  
  newProcList = reader.getProcessInfo()
  
  newProcListSet = set([ process for process in newProcList ])
  procListSet = set([process for process in procList ])
  
  newProc = newProcListSet.difference(procListSet)
  closedProc = procListSet.difference(newProcListSet)
  procList = newProcList 
  
  #color all green processes with default background
  defaultBgColor = app.palette().color(QtGui.QPalette.Base)  
  for proc in greenTopLevelItems:
    for column in xrange(greenTopLevelItems[proc].columnCount()):
      greenTopLevelItems[proc].setBackgroundColor(column, defaultBgColor)
  greenTopLevelItems.clear()
 
  #delete all red widgetItems
  for proc in redTopLevelItems:
    for topLevelIndex in xrange(mainUi.processTreeWidget.topLevelItemCount()):
      topLevelItem = mainUi.processTreeWidget.topLevelItem(topLevelIndex)
      delChild(topLevelItem, redTopLevelItems[proc])
      if topLevelItem == redTopLevelItems[proc]:
        mainUi.processTreeWidget.takeTopLevelItem(topLevelIndex)
        
  redTopLevelItems.clear()
  
  #create new items and mark items to be deleted red
  #draw tree hierarchy of processes
  for proc in newProc:
    addProcessAndParents(proc, procList)


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
    redTopLevelItems[proc] = treeProcesses[proc]
   
      
  #color all deleted processed red 
  for proc in redTopLevelItems:
    for column in xrange(redTopLevelItems[proc].columnCount()):
      redTopLevelItems[proc].setBackgroundColor(column, QtGui.QColor(255, 0, 0))
  
  #update status information about the processes  
  for proc in procList:   
    treeProcesses[proc].setData(0, 0, procList[proc]["name"])
    treeProcesses[proc].setData(1, 0, str(proc))
    treeProcesses[proc].setData(2, 0, procList[proc]["cpuUsage"])
    treeProcesses[proc].setData(3, 0, procList[proc]["cmdline"])
    treeProcesses[proc].setData(4, 0, procList[proc]["uid"])
    treeProcesses[proc].setData(5, 0, procList[proc]["wchan"])
    treeProcesses[proc].setData(6, 0, procList[proc]["nfThreads"])

  for proc in closedProc:
    del treeProcesses[proc]



  #color all new processes 'green'
  if firstUpdate == False:
    for proc in greenTopLevelItems:
      item = greenTopLevelItems[proc]
      for column in xrange(item.columnCount()):
        item.setBackgroundColor(column, QtGui.QColor(0, 255, 0))
    
  if (len(closedProc) > 0) or (len(newProc) > 0):
    expandAll()
  
  for _ui in singleProcessUiList:
    singleProcessUiList[_ui].update(reader)
    
  #update CPU plots
  systemOverviewUiWindow.update()
  
  #network plots
  networkOverviewUi.update()
    
  #update the cpu graph
  try:
    cpuUsageHistory.append(reader.overallUserCpuUsage()+
                           reader.overallSystemCpuUsage()+
                           reader.overallIoWaitCpuUsage()+
                           reader.overallIrqCpuUsage())
    cpuUsageHistory.pop(0)
    
    
    cpuUsageSystemHistory.append(reader.overallSystemCpuUsage()+
                                 reader.overallIoWaitCpuUsage()+
                                 reader.overallIrqCpuUsage())
    cpuUsageSystemHistory.pop(0)
    
    
    cpuUsageIoWaitHistory.append(reader.overallIoWaitCpuUsage() + 
                                 reader.overallIrqCpuUsage())
    cpuUsageIoWaitHistory.pop(0)
    
    
    cpuUsageIrqHistory.append(reader.overallIrqCpuUsage())
    cpuUsageIrqHistory.pop(0)
    


                                 
    curveCpuHist.setData(range(int(settings["historySampleCount"])), cpuUsageHistory)
    curveCpuSystemHist.setData(range(int(settings["historySampleCount"])), cpuUsageSystemHistory)
    curveIoWaitHist.setData(range(int(settings["historySampleCount"])), cpuUsageIoWaitHistory)
    curveIrqHist.setData(range(int(settings["historySampleCount"])), cpuUsageIrqHistory)
    mainUi.qwtPlotOverallCpuHist.replot()
    
  except:
    import traceback
    print traceback.format_exc()
  
  firstUpdate = False

def insertNewReaderUpdate(newReader):
  """insert a fresh reader object into the GUI and update """
  if g_signaller is not None:
    g_signaller.doSignal()
  global reader #pylint: disable-msg=W0603
  reader = copy.deepcopy(newReader)
  
def initStorageDepth():
  """init the storage depth in the GUI"""
  global cpuUsageHistory  #pylint: disable-msg=W0603
  global cpuUsageSystemHistory #pylint: disable-msg=W0603
  global cpuUsageIoWaitHistory #pylint: disable-msg=W0603
  global cpuUsageIrqHistory  #pylint: disable-msg=W0603
  
  cpuUsageHistory = [0] * int(settings["historySampleCount"])
  cpuUsageSystemHistory = [0] * int(settings["historySampleCount"])
  cpuUsageIoWaitHistory = [0] * int(settings["historySampleCount"])
  cpuUsageIrqHistory = [0] * int(settings["historySampleCount"])  
  
def setColumnWidths():
  """set the columnwidths"""
  for headerSection in range(mainUi.processTreeWidget.header().count()):
    try:
      width = int(settings["columnWidths"][headerSection])
    except:
      width = 150
    mainUi.processTreeWidget.header().resizeSection(headerSection, width)
    
def applyNewSettings():
  """apply new settings to the GUI """
  setFontSize(int(settings["fontSize"]))
  initStorageDepth()
  setColumnWidths()
  

def setupMainUi(newSettings):
  """setup the GUI"""
  global settings #pylint: disable-msg=W0603
  settings = copy.deepcopy(newSettings)
  global app #pylint: disable-msg=W0603
  app = QtGui.QApplication(sys.argv)
  app.setStyle("Windows")
  global MainWindow #pylint: disable-msg=W0603
  MainWindow = QtGui.QMainWindow()
  global mainUi #pylint: disable-msg=W0603
  mainUi = ui.main.Ui_MainWindow()
  mainUi.setupUi(MainWindow)
  
  prepareUI()
  MainWindow.show()
  #wait for a fresh reader
  while reader == None:
    print "wait for a reader"
    time.sleep(0.1)
  
  global systemOverviewUiWindow #pylint: disable-msg=W0603
  systemOverviewUiWindow = systemoverviewui.systemOverviewUi(reader.getCpuCount(), 
                                                     int(settings["historySampleCount"]), reader)
  global networkOverviewUi #pylint: disable-msg=W0603
  networkOverviewUi = networkoverview.networkOverviewUi(reader.getNetworkCards(), 
                                                        int(settings["historySampleCount"]), reader)
  global systemOverviewUiWindow #pylint: disable-msg=W0603
  systemOverviewUiWindow.setFontSize(int(settings["fontSize"]))
  
  global networkOverviewUi #pylint: disable-msg=W0603
  networkOverviewUi.setFontSize(int(settings["fontSize"]))
  
  #updateUI()
  
def runMainUi():
  """run the GUI event loop"""  
  sys.exit(app.exec_())

