import procreader.reader
import ui.main
import procutils
import os
import singleprocess
import systemoverview
import configobj
import feedback
import settings as settingsMenu
import plotobjects
import networkoverview
from PyQt4 import QtCore, QtGui
import PyQt4.Qwt5 as Qwt

import sys

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
    selectedItem = mainUi.processTreeWidget.selectedItems()[0]
    process = selectedItem.data(1,0).toString()
    procutils.killProcessHard(process)
  elif action is mainUi.actionKill_process_tree:
    selectedItem = mainUi.processTreeWidget.selectedItems()[0]
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
    selectedItem = mainUi.processTreeWidget.selectedItems()[0]
    process = str(selectedItem.data(1,0).toString())
    if singleProcessUiList.has_key(process):
      singleProcessUiList[process].makeVisible()
    else:
      singleProcessUiList[process] = singleprocess.singleUi(process, procList[int(process)]["cmdline"], procList[int(process)]["name"], reader, int(settings["historySampleCount"]))
  elif action is mainUi.actionSaveSettings:
    saveSettings()
  elif action is mainUi.actionSent_your_feedback:
    data = "kernelversion: "+ procutils.readFullFile("/proc/version") + "\n"
    data += "Distro" + procutils.readFullFile("/etc/issue") + "\n"
    feedback.doFeedBack(data)
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
  
  
def prepareUI(mainUi):
  global timer
  mainUi.processTreeWidget.setColumnCount(8)
  
  mainUi.processTreeWidget.setHeaderLabels(["Process","PID","CPU","Command Line", "User", "Chan","#thread"])
  
  #create a timer
  timer = QtCore.QTimer(mainUi.processTreeWidget)
  QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), updateUI)
  QtCore.QObject.connect(mainUi.processTreeWidget, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), onContextMenu)
  QtCore.QObject.connect(mainUi.menuProcess,  QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuOptions,  QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuSettings, QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuYourFeedback, QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  QtCore.QObject.connect(mainUi.menuView, QtCore.SIGNAL('triggered(QAction*)'), performMenuAction)
  
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
  
  plot = plotobjects.procExpPlot(mainUi.qwtPlotOverallCpuHist)
  
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
  
  if procList[proc]["PPID"] > 0: #process has a parent
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
  global procList
  global treeProcesses, greenTopLevelItems, redTopLevelItems
  global mainUi
  global firstUpdate
  reader.doReadProcessInfo()
  procList, closedProc, newProc = reader.getProcessInfo()
  
  flat = False
  
  #color all green processes 'white'
  for proc in greenTopLevelItems:
    for column in xrange(greenTopLevelItems[proc].columnCount()):
      greenTopLevelItems[proc].setBackgroundColor(column, QtGui.QColor(255,255,255))
  greenTopLevelItems = {}
 
  #delete all red widgetItems
  if flat:
    for proc in redTopLevelItems:
      index = mainUi.processTreeWidget.indexOfTopLevelItem(redTopLevelItems[proc])  
      mainUi.processTreeWidget.takeTopLevelItem(index)
  else:
    for proc in redTopLevelItems:
      for topLevelIndex in xrange(mainUi.processTreeWidget.topLevelItemCount()):
        topLevelItem = mainUi.processTreeWidget.topLevelItem(topLevelIndex)
        delChild(topLevelItem, redTopLevelItems[proc])
        if topLevelItem == redTopLevelItems[proc]:
          mainUi.processTreeWidget.takeTopLevelItem(topLevelIndex)
        
  redTopLevelItems = {}
  
  #create new items and mark items to be deleted red
  if flat:
    for proc in newProc:
      treeProcesses[proc] = QtGui.QTreeWidgetItem([])
      greenTopLevelItems[proc] = treeProcesses[proc]
      mainUi.processTreeWidget.addTopLevelItem(treeProcesses[proc])    
  else:
    #draw tree hierarchy of processes
    for proc in newProc:
      widgetItem = addProcessAndParents(proc, procList)

  #copy processed to be deleted to the red list
  for proc in closedProc:
    redTopLevelItems[proc] = treeProcesses[proc]
   
      
  #color all deleted processed red 
  for proc in redTopLevelItems:
    for column in xrange(redTopLevelItems[proc].columnCount()):
      redTopLevelItems[proc].setBackgroundColor(column, QtGui.QColor(255,0,0))
  
  #update status information about the processes  
  for proc in procList:   
    treeProcesses[proc].setData(0, 0, procList[proc]["name"])
    treeProcesses[proc].setData(1, 0, str(proc))
    treeProcesses[proc].setData(2, 0, procList[proc]["cpuUsage"])
    treeProcesses[proc].setData(3, 0, procList[proc]["cmdline"])
    treeProcesses[proc].setData(4, 0, procList[proc]["uid"])
    treeProcesses[proc].setData(5, 0, procList[proc]["whan"])
    treeProcesses[proc].setData(6, 0, procList[proc]["nfThreads"])

  #color all new processes 'green'
  if firstUpdate == False:
    for proc in greenTopLevelItems:
      item = greenTopLevelItems[proc]
      for column in xrange(item.columnCount()):
        item.setBackgroundColor(column, QtGui.QColor(0,255,0))
    
  if flat == False:      
    if (len(closedProc) > 0) or (len(newProc) > 0):
      expandAll()
  
  for ui in singleProcessUiList:
    singleProcessUiList[ui].update()
    
  #update CPU plots
  systemOverviewUi.update()
  
  #network plots
  networkOverviewUi.update()
    
  #update the cpu graph
  try:
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
    
  except:
    import traceback
    print traceback.format_exc()
  
  firstUpdate = False
  
app = QtGui.QApplication(sys.argv)
app.setStyle("Windows")
MainWindow = QtGui.QMainWindow()
mainUi = ui.main.Ui_MainWindow()
mainUi.setupUi(MainWindow)

prepareUI(mainUi)
loadSettings()

timer.start(int(settings["updateTimer"]))  

MainWindow.show()

reader = procreader.reader.procreader(int(settings["updateTimer"]), int(settings["historySampleCount"]))
if onlyUser:
  reader.setFilterUID(os.geteuid())

systemOverviewUi = systemoverview.systemOverviewUi(reader.getCpuCount(), int(settings["historySampleCount"]), reader)
networkOverviewUi = networkoverview.networkOverviewUi(reader.getNetworkCards(), int(settings["historySampleCount"]), reader)
  
updateUI()
sys.exit(app.exec_())

