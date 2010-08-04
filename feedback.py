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
      
