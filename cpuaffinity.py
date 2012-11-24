from PyQt4 import QtGui
import ui.cpuaffinity as affinityDialog
import subprocess
import procutils

def doAffinity(cpuCount, process):
  global ui
  Dialog = QtGui.QDialog()
  aff = affinityDialog.Ui_affinityDialog()
  aff.setupUi(Dialog)
  
  #get affinity of process
  affinityHexStr =subprocess.Popen(["taskset", "-p", str(process)], \
                                   stdout=subprocess.PIPE).communicate()[0].strip().split("affinity mask: ")[1]
  
  affinity = int(affinityHexStr, 16)

  #disable cpu checkboxes we do not have..
  for objName in aff.__dict__:
    if objName.find("checkBox_") != -1:
      cpuNr = int(objName.split("_")[1])
      if cpuNr < cpuCount:
        aff.__dict__[objName].setEnabled(True)
      else:
        aff.__dict__[objName].setEnabled(False)
  
  #check CPU checkboxes
  for cpu in xrange(cpuCount):
    for objName in aff.__dict__:
      if objName == "checkBox_%s" %cpu:
        if affinity & 2**cpu == 2**cpu:
          aff.__dict__[objName].setChecked(True)
        else:
          aff.__dict__[objName].setChecked(False)
          
  ui = aff
  Dialog.setModal(True) 
  Dialog.exec_()  

  #apply new affinity
  newAff = 0
  for cpu in xrange(cpuCount):
    for objName in aff.__dict__:
      if objName == "checkBox_%s" %cpu:
        if aff.__dict__[objName].isChecked():
          newAff = newAff | 2**cpu

  if affinity != newAff:
    proc = subprocess.Popen(["taskset", "-p", hex(newAff).replace("0x",""), str(process)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate()
    result = proc.returncode
    if result != 0:
      procutils.message("Setting process %s affinity value to %s failed" %(process, hex(newAff).replace("0x","")))
  
  
  