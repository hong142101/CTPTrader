# encoding: UTF-8

import json
import csv
import os
from collections import OrderedDict

from PyQt4 import QtGui, QtCore

from eventEngine import *
from vtFunction import *
from vtGateway import *
from allText import *


# ----------------------------------------------------------------------
def loadFont():
    """载入字体设置"""
    family = u'微软雅黑'
    size = 10
    font = QtGui.QFont(family, size)
    return font


BASIC_FONT = loadFont()


########################################################################
class BasicCell(QtGui.QTableWidgetItem):
    """基础的单元格"""

    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(BasicCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)

    # ----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        if text == '0' or text == '0.0':
            self.setText('0')
        else:
            self.setText(text)


########################################################################
class NumCell(QtGui.QTableWidgetItem):
    """用来显示数字的单元格"""

    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(NumCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)

    # ----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        # 考虑到NumCell主要用来显示OrderID和TradeID之类的整数字段，
        # 这里的数据转化方式使用int类型。但是由于部分交易接口的委托
        # 号和成交号可能不是纯数字的形式，因此补充了一个try...except
        try:
            num = int(text)
            self.setData(QtCore.Qt.DisplayRole, num)
        except ValueError:
            self.setText(text)


########################################################################
class DirectionCell(QtGui.QTableWidgetItem):
    """用来显示买卖方向的单元格"""

    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(DirectionCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)

    # ----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        if text == DIRECTION_LONG or text == DIRECTION_NET:
            self.setForeground(QtGui.QColor('red'))
        elif text == DIRECTION_SHORT:
            self.setForeground(QtGui.QColor('green'))
        self.setText(text)


########################################################################
class NameCell(QtGui.QTableWidgetItem):
    """用来显示合约中文的单元格"""

    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(NameCell, self).__init__()

        self.mainEngine = mainEngine
        self.data = None

        if text:
            self.setContent(text)

    # ----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        if self.mainEngine:
            # 首先尝试正常获取合约对象
            contract = self.mainEngine.getContract(text)

            # 如果能读取合约信息
            if contract:
                self.setText(contract.name)


########################################################################
class BasicMonitor(QtGui.QTableWidget):
    """
    基础监控
    
    headerDict中的值对应的字典格式如下
    {'chinese': u'中文名', 'cellType': BasicCell}
    
    """
    signal = QtCore.pyqtSignal(type(Event()))

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine=None, eventEngine=None, parent=None):
        """Constructor"""
        super(BasicMonitor, self).__init__(parent)

        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        # 保存表头标签用
        self.headerDict = OrderedDict()  # 有序字典，key是英文名，value是对应的配置字典
        self.headerList = []  # 对应self.headerDict.keys()

        # 保存相关数据用
        self.dataDict = {}  # 字典，key是字段对应的数据，value是保存相关单元格的字典
        self.dataKey = ''  # 字典键对应的数据字段

        # 监控的事件类型
        self.eventType = ''

        # 字体
        self.font = None

        # 保存数据对象到单元格
        self.saveData = False

        # 默认不允许根据表头进行排序，需要的组件可以开启
        self.sorting = False

    # ----------------------------------------------------------------------
    def setHeaderDict(self, headerDict):
        """设置表头有序字典"""
        self.headerDict = headerDict
        self.headerList = list(headerDict.keys())

    # ----------------------------------------------------------------------
    def setDataKey(self, dataKey):
        """设置数据字典的键"""
        self.dataKey = dataKey

    # ----------------------------------------------------------------------
    def setEventType(self, eventType):
        """设置监控的事件类型"""
        self.eventType = eventType

    # ----------------------------------------------------------------------
    def setFont(self, font):
        """设置字体"""
        self.font = font

    # ----------------------------------------------------------------------
    def setSaveData(self, saveData):
        """设置是否要保存数据到单元格"""
        self.saveData = saveData

    # ----------------------------------------------------------------------
    def initTable(self):
        """初始化表格"""
        # 设置表格的列数
        col = len(self.headerDict)
        self.setColumnCount(col)

        # 设置列表头
        labels = [d['chinese'] for d in self.headerDict.values()]
        self.setHorizontalHeaderLabels(labels)

        # 关闭左边的垂直表头
        self.verticalHeader().setVisible(False)

        # 设为不可编辑
        # self.setEditTriggers(self.NoEditTriggers)

        # 设为行交替颜色
        self.setAlternatingRowColors(True)

        # 设置允许排序
        self.setSortingEnabled(self.sorting)

    # ----------------------------------------------------------------------
    def registerEvent(self):
        """注册GUI更新相关的事件监听"""
        self.signal.connect(self.updateEvent)
        self.eventEngine.register(self.eventType, self.signal.emit)

    # ----------------------------------------------------------------------
    def updateEvent(self, event):
        """收到事件更新"""
        data = event.dict_['data']
        self.updateData(data)

    # ----------------------------------------------------------------------
    def updateData(self, data):
        """将数据更新到表格中"""
        # 如果允许了排序功能，则插入数据前必须关闭，否则插入新的数据会变乱
        if self.sorting:
            self.setSortingEnabled(False)

        # 如果设置了dataKey，则采用存量更新模式
        if self.dataKey:
            key = data.__getattribute__(self.dataKey)
            # 如果键在数据字典中不存在，则先插入新的一行，并创建对应单元格
            if key not in self.dataDict:
                self.insertRow(0)
                d = {}
                for n, header in enumerate(self.headerList):
                    content = safeUnicode(data.__getattribute__(header))
                    cellType = self.headerDict[header]['cellType']
                    cell = cellType(content, self.mainEngine)

                    if self.font:
                        cell.setFont(self.font)  # 如果设置了特殊字体，则进行单元格设置

                    if self.saveData:  # 如果设置了保存数据对象，则进行对象保存
                        cell.data = data

                    self.setItem(0, n, cell)
                    d[header] = cell
                self.dataDict[key] = d
            # 否则如果已经存在，则直接更新相关单元格
            else:
                d = self.dataDict[key]
                for header in self.headerList:
                    content = safeUnicode(data.__getattribute__(header))
                    cell = d[header]
                    cell.setContent(content)

                    if self.saveData:  # 如果设置了保存数据对象，则进行对象保存
                        cell.data = data
                        # 否则采用增量更新模式
        else:
            self.insertRow(0)
            for n, header in enumerate(self.headerList):
                content = safeUnicode(data.__getattribute__(header))
                cellType = self.headerDict[header]['cellType']
                cell = cellType(content, self.mainEngine)

                if self.font:
                    cell.setFont(self.font)

                if self.saveData:
                    cell.data = data

                self.setItem(0, n, cell)

                # 调整列宽
        self.resizeColumns()

        # 重新打开排序
        if self.sorting:
            self.setSortingEnabled(True)

    # ----------------------------------------------------------------------
    def resizeColumns(self):
        """调整各列的大小"""
        self.horizontalHeader().resizeSections(QtGui.QHeaderView.ResizeToContents)

    # ----------------------------------------------------------------------
    def setSorting(self, sorting):
        """设置是否允许根据表头排序"""
        self.sorting = sorting


########################################################################
class LogMonitor(BasicMonitor):
    """日志监控"""

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(LogMonitor, self).__init__(mainEngine, eventEngine, parent)

        d = OrderedDict()
        d['logTime'] = {'chinese': TIME, 'cellType': BasicCell}
        d['logContent'] = {'chinese': CONTENT, 'cellType': BasicCell}
        d['gatewayName'] = {'chinese': GATEWAY, 'cellType': BasicCell}
        self.setHeaderDict(d)

        self.setEventType(EVENT_LOG)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.registerEvent()


########################################################################
class ErrorMonitor(BasicMonitor):
    """错误监控"""

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(ErrorMonitor, self).__init__(mainEngine, eventEngine, parent)

        d = OrderedDict()
        d['errorTime'] = {'chinese': TIME, 'cellType': BasicCell}
        d['errorID'] = {'chinese': ERROR_CODE, 'cellType': BasicCell}
        d['errorMsg'] = {'chinese': ERROR_MESSAGE, 'cellType': BasicCell}
        d['gatewayName'] = {'chinese': GATEWAY, 'cellType': BasicCell}
        self.setHeaderDict(d)

        self.setEventType(EVENT_ERROR)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.registerEvent()


########################################################################
class TradeMonitor(BasicMonitor):
    """成交监控"""

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(TradeMonitor, self).__init__(mainEngine, eventEngine, parent)

        d = OrderedDict()
        d['tradeID'] = {'chinese': TRADE_ID, 'cellType': NumCell}
        d['orderID'] = {'chinese': ORDER_ID, 'cellType': NumCell}
        d['symbol'] = {'chinese': CONTRACT_SYMBOL, 'cellType': BasicCell}
        d['vtSymbol'] = {'chinese': CONTRACT_NAME, 'cellType': NameCell}
        d['direction'] = {'chinese': DIRECTION, 'cellType': DirectionCell}
        d['offset'] = {'chinese': OFFSET, 'cellType': BasicCell}
        d['price'] = {'chinese': PRICE, 'cellType': BasicCell}
        d['volume'] = {'chinese': VOLUME, 'cellType': BasicCell}
        d['tradeTime'] = {'chinese': TRADE_TIME, 'cellType': BasicCell}
        d['gatewayName'] = {'chinese': GATEWAY, 'cellType': BasicCell}
        self.setHeaderDict(d)

        self.setEventType(EVENT_TRADE)
        self.setFont(BASIC_FONT)
        self.setSorting(True)

        self.initTable()
        self.registerEvent()


########################################################################
class OrderMonitor(BasicMonitor):
    """委托监控"""

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(OrderMonitor, self).__init__(mainEngine, eventEngine, parent)

        self.mainEngine = mainEngine

        d = OrderedDict()
        d['orderID'] = {'chinese': ORDER_ID, 'cellType': NumCell}
        d['symbol'] = {'chinese': CONTRACT_SYMBOL, 'cellType': BasicCell}
        d['vtSymbol'] = {'chinese': CONTRACT_NAME, 'cellType': NameCell}
        d['direction'] = {'chinese': DIRECTION, 'cellType': DirectionCell}
        d['offset'] = {'chinese': OFFSET, 'cellType': BasicCell}
        d['price'] = {'chinese': PRICE, 'cellType': BasicCell}
        d['totalVolume'] = {'chinese': ORDER_VOLUME, 'cellType': BasicCell}
        d['tradedVolume'] = {'chinese': TRADED_VOLUME, 'cellType': BasicCell}
        d['status'] = {'chinese': ORDER_STATUS, 'cellType': BasicCell}
        d['orderTime'] = {'chinese': ORDER_TIME, 'cellType': BasicCell}
        d['cancelTime'] = {'chinese': CANCEL_TIME, 'cellType': BasicCell}
        # d['frontID'] = {'chinese':FRONT_ID, 'cellType':BasicCell}
        # 考虑到在vn.trader中，ctpGateway的报单号应该是始终递增的，因此这里可以忽略
        # d['sessionID'] = {'chinese':SESSION_ID, 'cellType':BasicCell}
        d['gatewayName'] = {'chinese': GATEWAY, 'cellType': BasicCell}
        self.setHeaderDict(d)

        self.setDataKey('vtOrderID')
        self.setEventType(EVENT_ORDER)
        self.setFont(BASIC_FONT)
        self.setSaveData(True)
        self.setSorting(True)

        self.initTable()
        self.registerEvent()


########################################################################
class PositionMonitor(BasicMonitor):
    """持仓监控"""

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(PositionMonitor, self).__init__(mainEngine, eventEngine, parent)

        d = OrderedDict()
        d['symbol'] = {'chinese': CONTRACT_SYMBOL, 'cellType': BasicCell}
        d['vtSymbol'] = {'chinese': CONTRACT_NAME, 'cellType': NameCell}
        d['direction'] = {'chinese': DIRECTION, 'cellType': DirectionCell}
        d['position'] = {'chinese': POSITION, 'cellType': BasicCell}
        d['ydPosition'] = {'chinese': YD_POSITION, 'cellType': BasicCell}
        d['frozen'] = {'chinese': FROZEN, 'cellType': BasicCell}
        d['price'] = {'chinese': USE_MARGIN, 'cellType': BasicCell}
        d['positionProfit'] = {'chinese': POSITION_PROFIT, 'cellType': BasicCell}
        d['gatewayName'] = {'chinese': GATEWAY, 'cellType': BasicCell}
        self.setHeaderDict(d)

        self.setDataKey('vtPositionName')
        self.setEventType(EVENT_POSITION)
        self.setFont(BASIC_FONT)
        self.setSaveData(True)

        self.initTable()
        self.registerEvent()


########################################################################
class AccountMonitor(BasicMonitor):
    """账户监控"""

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(AccountMonitor, self).__init__(mainEngine, eventEngine, parent)

        d = OrderedDict()
        d['accountID'] = {'chinese': ACCOUNT_ID, 'cellType': BasicCell}
        d['preBalance'] = {'chinese': PRE_BALANCE, 'cellType': BasicCell}
        d['balance'] = {'chinese': BALANCE, 'cellType': BasicCell}
        d['available'] = {'chinese': AVAILABLE, 'cellType': BasicCell}
        d['commission'] = {'chinese': COMMISSION, 'cellType': BasicCell}
        d['margin'] = {'chinese': MARGIN, 'cellType': BasicCell}
        d['closeProfit'] = {'chinese': CLOSE_PROFIT, 'cellType': BasicCell}
        d['positionProfit'] = {'chinese': POSITION_PROFIT, 'cellType': BasicCell}
        d['gatewayName'] = {'chinese': GATEWAY, 'cellType': BasicCell}
        self.setHeaderDict(d)

        self.setDataKey('vtAccountID')
        self.setEventType(EVENT_ACCOUNT)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.registerEvent()

