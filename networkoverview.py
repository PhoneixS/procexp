#
# Display network overview
#

from PyQt4 import QtCore, QtGui
import PyQt4.Qwt5 as Qwt
import ui.networkinformation
import plotobjects


class networkPlotObject(object):
  def __init__(self, plot, depth, reader, card, scale):
    self.__curveNetInHist__ = plotobjects.niceCurve("Network In History", 
                             1 ,QtGui.QColor(241,254,1), QtGui.QColor(181,190,1), 
                             plot)
    self.__curveNetOutHist__ = plotobjects.niceCurve("Network Out History", 
                             1, QtGui.QColor(28,255,255),QtGui.QColor(0,168,168), 
                             plot)
                             
    self.__depth__ = depth
    self.__reader__ = reader
    self.__first__ = False
    self.__plot__ = plot
    self.__card__ = card
    
    #adapt the network plot
    self.__adaptednetworkplot = plotobjects.procExpPlot(self.__plot__, scale)
    
    self.__networkInUsageHistory__ = [0] * int(self.__depth__)
    self.__networkOutUsageHistory__ = [0] * int(self.__depth__)
    
  def update(self):
    values = self.__reader__.getNetworkCardUsage(self.__card__)
    
    #print self.__networkInUsageHistory__
    self.__networkInUsageHistory__.append(values[0])
    self.__networkOutUsageHistory__.append(values[1])
    self.__networkInUsageHistory__ = self.__networkInUsageHistory__[1:]
    self.__networkOutUsageHistory__ = self.__networkOutUsageHistory__[1:]
    self.__curveNetInHist__ .setData(range(self.__depth__), self.__networkInUsageHistory__)
    self.__curveNetOutHist__ .setData(range(self.__depth__), self.__networkOutUsageHistory__)
    self.__plot__.replot()
                             

class networkOverviewUi(object):
  def __init__(self, networkCards, depth, reader):
    self.__reader__ = reader
    self.__depth__ = depth
    self.__dialog__ = QtGui.QDialog()
    self.__ui__ = ui.networkinformation.Ui_Dialog()
    self.__ui__.setupUi(self.__dialog__)
    self.__networkCards__ = networkCards
    self.__netPlotArray = []
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_00, self.__ui__.qwtPlotNetworkCardHistory_00]]    
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_01, self.__ui__.qwtPlotNetworkCardHistory_01]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_02, self.__ui__.qwtPlotNetworkCardHistory_02]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_03, self.__ui__.qwtPlotNetworkCardHistory_03]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_04, self.__ui__.qwtPlotNetworkCardHistory_04]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_05, self.__ui__.qwtPlotNetworkCardHistory_05]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_06, self.__ui__.qwtPlotNetworkCardHistory_06]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_07, self.__ui__.qwtPlotNetworkCardHistory_07]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_08, self.__ui__.qwtPlotNetworkCardHistory_08]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_09, self.__ui__.qwtPlotNetworkCardHistory_09]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_10, self.__ui__.qwtPlotNetworkCardHistory_10]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_11, self.__ui__.qwtPlotNetworkCardHistory_11]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_12, self.__ui__.qwtPlotNetworkCardHistory_12]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_13, self.__ui__.qwtPlotNetworkCardHistory_13]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_14, self.__ui__.qwtPlotNetworkCardHistory_14]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_15, self.__ui__.qwtPlotNetworkCardHistory_15]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_16, self.__ui__.qwtPlotNetworkCardHistory_16]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_17, self.__ui__.qwtPlotNetworkCardHistory_17]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_18, self.__ui__.qwtPlotNetworkCardHistory_18]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_19, self.__ui__.qwtPlotNetworkCardHistory_19]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_20, self.__ui__.qwtPlotNetworkCardHistory_20]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_21, self.__ui__.qwtPlotNetworkCardHistory_21]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_22, self.__ui__.qwtPlotNetworkCardHistory_22]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_23, self.__ui__.qwtPlotNetworkCardHistory_23]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_24, self.__ui__.qwtPlotNetworkCardHistory_24]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_25, self.__ui__.qwtPlotNetworkCardHistory_25]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_26, self.__ui__.qwtPlotNetworkCardHistory_26]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_27, self.__ui__.qwtPlotNetworkCardHistory_27]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_28, self.__ui__.qwtPlotNetworkCardHistory_28]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_29, self.__ui__.qwtPlotNetworkCardHistory_29]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_30, self.__ui__.qwtPlotNetworkCardHistory_30]]
    self.__netPlotArray += [[self.__ui__.groupBoxNetworkCard_31, self.__ui__.qwtPlotNetworkCardHistory_31]]
    self.__tabs__ = {}

    
    
    for card in xrange(32):
      if card+1 > len(self.__networkCards__):
        self.__netPlotArray[card][0].setVisible(False)
        self.__netPlotArray[card].append(False)
      else:
        self.__netPlotArray[card].append(True)
        
    idx = 0
    for cardName in self.__networkCards__:
      if self.__netPlotArray[idx][2] == True:
        
        speed = self.__networkCards__[cardName]["speed"]
        if speed is not None:
          scale = plotobjects.scaleObject()
          scale.min = 0
          scale.max = (speed / 8.0) * 1024.0 * 1024.0 * 0.8 #Speed in Mbit/s, rule of thumb 80% achievable of max theoretical bandwidth..
        else:
          scale = None #leads to autoscaling in graphs...

          
        self.__netPlotArray[idx].append(networkPlotObject(self.__netPlotArray[idx][1],
                                                         self.__depth__,
                                                         self.__reader__,
                                                         cardName,
                                                         scale))
        
        if speed is None:
          self.__netPlotArray[idx][0].setTitle(cardName+" / " + "??" + " MB/s")
        else:
          self.__netPlotArray[idx][0].setTitle(cardName+", ~" + str(round(scale.max / (1024.0*1024.0))) + " MB/s")
      idx +=1
      
    #create tab per network card
    for card in self.__networkCards__:
      tab = QtGui.QWidget()
      self.__tabs__[card] = [tab, 
                              [QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), 
                               QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), 
                               QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab)],
                              [QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), 
                               QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), 
                               QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab), QtGui.QLabel(tab)]] 
      self.__ui__.tabWidget.addTab(tab, "")
      self.__ui__.tabWidget.setTabText(self.__ui__.tabWidget.indexOf(tab), card)
      ymargin=20
      y = 10
      xoffs = 20
      for label in self.__tabs__[card][1][0:6]:
        label.setGeometry(QtCore.QRect(20, y, 130, 18))
        y += ymargin
      y=10
      for label in self.__tabs__[card][1][6:13]:
        label.setGeometry(QtCore.QRect(320, y, 130, 18))
        y += ymargin
      self.__tabs__[card][1][0].setText("Rec Errors")
      self.__tabs__[card][1][1].setText("Rec Drops")
      self.__tabs__[card][1][2].setText("Send Errors")
      self.__tabs__[card][1][3].setText("Send Drops")
      self.__tabs__[card][1][4].setText("Send Coll")
      self.__tabs__[card][1][5].setText("Rec bytes")
      self.__tabs__[card][1][6].setText("Send bytes")
      self.__tabs__[card][1][7].setText("Rec packets")
      self.__tabs__[card][1][8].setText("Send packets")
      self.__tabs__[card][1][9].setText("Rec bytes/s")
      self.__tabs__[card][1][10].setText("Send bytes/s")
      self.__tabs__[card][1][11].setText("Avg rec packet size")
      self.__tabs__[card][1][12].setText("Avg snd packet size")
      
      y = 10
      for label in self.__tabs__[card][2][0:6]:
        label.setGeometry(QtCore.QRect(170, y, 80, 18))
        y += ymargin
        label.setText("0")
      y=10
      for label in self.__tabs__[card][2][6:13]:
        label.setGeometry(QtCore.QRect(470, y, 80, 18))
        y += ymargin
        label.setText("0")
      

      
  def show(self):
    self.__dialog__.show()
    self.__dialog__.setVisible(True)    
    
  def update(self):
    for plot in xrange(32):
      if plot+1 <= len(self.__networkCards__):
        self.__netPlotArray[plot][3].update()
    
    for card in self.__networkCards__:
      networkStat = self.__reader__.getNetworkCardData(card)
      
      self.__tabs__[card][2][0].setText(str(networkStat["recerrors"]))
      self.__tabs__[card][2][1].setText(str(networkStat["recdrops"]))
      self.__tabs__[card][2][2].setText(str(networkStat["senderrors"]))
      self.__tabs__[card][2][3].setText(str(networkStat["senddrops"]))
      self.__tabs__[card][2][4].setText(str(networkStat["sendcoll"]))
      self.__tabs__[card][2][5].setText(str(networkStat["recbytes"]))
      self.__tabs__[card][2][6].setText(str(networkStat["sendbytes"]))
      self.__tabs__[card][2][7].setText(str(networkStat["recpackets"]))
      self.__tabs__[card][2][8].setText(str(networkStat["sendpackets"]))
      try:
        self.__tabs__[card][2][11].setText(str(int(networkStat["recbytes"] / (networkStat["recpackets"]*1.0))))
      except:
        self.__tabs__[card][2][11].setText("0")
      try:
        self.__tabs__[card][2][12].setText(str(int(networkStat["sendbytes"] / (networkStat["sendpackets"]*1.0))))
      except:
        self.__tabs__[card][2][12].setText("0")
        
    
