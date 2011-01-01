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
import os
import configobj
import ui.procexpui
import utils
import communication.tcp
import time
import server
import procreader.reader
from optparse import OptionParser

g_stop = False
defaultSettings = \
{"fontSize": 10, 
 "columnWidths": [100,60,40,100,30,30,30,30],
 "updateTimer": 1000,
 "historySampleCount": 200
}

def produceData(theServer):
  """produce data for clients"""
  reader = procreader.reader.procreader(int("1000"), int("200"))
  stop = False
  if True:#onlyUser:
    reader.setFilterUID(os.geteuid())
  while stop == False:
    try:
      reader.doReadProcessInfo()
      theServer.sendData(reader)
      time.sleep(1000 / 1000)
    except:
      stop = True
      
@utils.asynchronous(None)
def getData():
  """get data from a procexp server"""
  client = None
  while g_stop == False:
    while g_stop == False and client == None:
      try:
        client = communication.tcp.Client(("127.0.0.1", 4000))
      except communication.tcp.TCPError:
        time.sleep(0.1)
    while g_stop == False:
      try:
        newReader = client.receive()
        ui.procexpui.insertNewReaderUpdate(newReader)
      except:
        client = None
        break
         
def loadSettings():
  """load settings"""
  settings = {}
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
   
  #load default settings for undefined settings
  for item in defaultSettings:
    if settings.has_key(item):
      pass
    else:
      settings[item] = defaultSettings[item]
  return settings

def runAsGui():
  """run the GUI part of the linux process explorer"""
  try:
    ui_settings = loadSettings()
    getData()    
    ui.procexpui.setupMainUi(ui_settings)
    ui.procexpui.applyNewSettings()
    ui.procexpui.runMainUi()
    global g_stop #pylint: disable-msg=W0603
    g_stop = True
  except:
    import traceback
    print traceback.format_exc()

def main():
  """main"""
  usage = "usage: %prog [options]"
  parser = OptionParser(usage)
  
  parser.add_option("-c", "--client", dest="client", action="store_const", const=True,
                    help="run as a procexp client")    
  parser.add_option("-s", "--server", dest="server", action="store_const", const=True,
                    help="run as a procexp server")    
                    
  (options, _args) = parser.parse_args()
  
  if options.client:
    runAsGui()
  elif options.server:
    import socket
    PORTNUMBER = 4000
    address = (socket.gethostname(), PORTNUMBER)
    procexpserver = server.procexpServer(address)
    procexpserver.doServe()
    print "process explorer server started."
    produceData(procexpserver)
    print "process explorer server ended."
    procexpserver.stopServer()

if __name__ == "__main__":
  main()
