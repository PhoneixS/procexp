from PyQt4 import QtCore, QtGui
import ui.feedback
import ui.feedbackok
import ui.feedbacknok
import time
import socket
import traceback

def doFeedBack(data = None):
  Dialog = QtGui.QDialog()
  feedbackui = ui.feedback.Ui_Dialog()
  feedbackui.setupUi(Dialog)
  feedbackui.generatedInfoText.setPlainText(data)
  Dialog.setModal(True)
  Dialog.exec_()
  
  customText = str(feedbackui.yourFeedbackTextEdit.toPlainText())
  if Dialog.result() == 1:
    #user wants to give feedback
    
    try:
      s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
      s.connect(("www.wolff-online.nl",80))
      s.send("PROCEXP FEEDBACK\n" + data + "\nCUSTOM REMARK\n"+ customText)
      s.close()
      ok  = True
    except:
      print "Feedback sent failed..."
      print "please try again later"
      print traceback.format_exc()
      ok  = False
    
    Dialog = QtGui.QDialog()
    if ok:
      feedbackui = ui.feedbackok.Ui_Dialog()
    else:
      feedbackui = ui.feedbacknok.Ui_Dialog()
    feedbackui.setupUi(Dialog)
    Dialog.setModal(True)
    Dialog.exec_()
      
