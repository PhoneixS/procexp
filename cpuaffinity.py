from PyQt4 import QtCore, QtGui
import ui.cpuaffinity as affinityDialog

def doAffinity():
  global ui
  Dialog = QtGui.QDialog()
  aff = affinityDialog.Ui_affinityDialog()
  aff.setupUi(Dialog)
  ui = aff
  Dialog.setModal(True) 
  Dialog.exec_()  


