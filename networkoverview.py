#
# Display network overview
#

from PyQt4 import QtCore, QtGui
import PyQt4.Qwt5 as Qwt
import ui.networkinformation
import plotobjects


class networkPlotObject(object):
  def __init__(self, plot, depth, reader, card):
    self.__curveNetInHist__ = plotobjects.niceCurve("Network In History", 
                             1 ,QtGui.QColor(217,137,123), QtGui.QColor(180,70,50), 
                             plot)
    self.__curveNetOutHist__ = plotobjects.niceCurve("Network Out History", 
                             1, QtGui.QColor(0,0,255),QtGui.QColor(0,0,127), 
                             plot)
                             
    self.__depth__ = depth
    self.__reader__ = reader
    self.__first__ = False
    self.__plot__ = plot
    self.__card__ = card
    #adapt the network plot
    
    self.__networkInUsageHistory__ = [0] * int(self.__depth__)
    self.__networkOutUsageHistory__ = [0] * int(self.__depth__)
    
  def update(self):
    values = self.__reader__.getNetworkCardUsage(self.__card__)
    
    if self.__first__ == False:
      self.__first__ = True
      scale = plotobjects.scaleObject()
      scale.min = 0
      scale.max = values[0]
      self.__adaptednetworkplot = plotobjects.procExpPlot(self.__plot__, scale)
    
    
    self.__networkInUsageHistory__.append(values[0])
    self.__networkOutUsageHistory__.append(values[1])
    self.__networkInUsageHistory__ = self.__networkInUsageHistory__[1:]
    self.__networkOutUsageHistory__ = self.__networkOutUsageHistory__[1:]
    self.__curveNetInHist__ .setData(range(self.__depth__), self.__networkInUsageHistory__)
    self.__curveNetOutHist__ .setData(range(self.__depth__), self.__networkOutUsageHistory__)
    self.__plot__.replot()
                             

class networkOverviewUi(object):
  def __init__(self, networkCardCount, depth, reader):
    self.__reader__ = reader
    self.__depth__ = depth
    self.__dialog__ = QtGui.QDialog()
    self.__ui__ = ui.networkinformation.Ui_Dialog()
    self.__ui__.setupUi(self.__dialog__)
    self.__networkCardCount__ = networkCardCount
    self.__netPlotArray = []
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_00]]    
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_01]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_02]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_03]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_04]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_05]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_06]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_07]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_08]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_09]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_10]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_11]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_12]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_13]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_14]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_15]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_16]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_17]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_18]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_19]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_20]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_21]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_22]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_23]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_24]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_25]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_26]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_27]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_28]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_29]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_30]]
    self.__netPlotArray += [[self.__ui__.qwtPlotNetworkCardHistory_31]]

    
    
    for card in xrange(32):
      if card+1 > self.__networkCardCount__:
        self.__netPlotArray[card][0].setVisible(False)
        self.__netPlotArray[card].append(False)
      else:
        self.__netPlotArray[card].append(True)
        
      if self.__netPlotArray[card][1] == True:
        self.__netPlotArray[card].append(networkPlotObject(self.__netPlotArray[card][0],
                                                         self.__depth__,
                                                         self.__reader__,
                                                         card))
  def show(self):
    self.__dialog__.show()
    self.__dialog__.setVisible(True)    
    
  def update(self):
    for plot in xrange(32):
      if plot+1 <= self.__networkCardCount__:
        self.__netPlotArray[plot][2].update()
    
