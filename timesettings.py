from PyQt4 import QtCore, QtGui
import ui.historydepth


global ui

def onChange():
  global ui
  
  try:
    nfSamples = int(str(ui.lineEditNfSamples.displayText())) * 1.0
    timesSecond = float(str(ui.lineEditTimesSecond.displayText()))
  
    ui.lineEditMinutes.setText(str(round(nfSamples / timesSecond / 60.0,2)))
    ui.lineEditDays.setText(str(round((nfSamples / timesSecond) / (24.0*60.0*60.0),2)))
    ui.lineEditHours.setText(str(round((nfSamples / timesSecond) / (60.0*60.0),2)))
  except:
    ui.lineEditMinutes.setText("?")
    ui.lineEditDays.setText("?")
    ui.lineEditHours.setText("?")
  

def doTimeSetings(millisecWait,depth):
  global ui
  Dialog = QtGui.QDialog()
  settings = ui.historydepth.Ui_Dialog()
  settings.setupUi(Dialog)
  ui = settings
  Dialog.setModal(True)
  QtCore.QObject.connect(settings.lineEditNfSamples,  QtCore.SIGNAL('textChanged (const QString&)'), onChange)
  QtCore.QObject.connect(settings.lineEditTimesSecond,  QtCore.SIGNAL('textChanged (const QString&)'), onChange)
  ui.lineEditTimesSecond.setText(str(float(1000.0 / (millisecWait * 1.0))))
  ui.lineEditNfSamples.setText(str(depth))
  Dialog.exec_()
  
  millisecWait = int(1000.0 / float(str(ui.lineEditTimesSecond.displayText())))
  depth = int(str(ui.lineEditNfSamples.displayText()))
  return(millisecWait, depth)
