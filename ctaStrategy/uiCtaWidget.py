# encoding: UTF-8

"""
CTA模块相关的GUI控制组件
"""

import time as t

from uiBasicWidget import QtGui, QtCore, BasicCell
from eventEngine import *
from vtGateway import *
from allText import *


########################################################################
class CtaValueMonitor(QtGui.QTableWidget):
    """参数监控"""

    # ----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(CtaValueMonitor, self).__init__(parent)

        self.keyCellDict = {}
        self.data = None
        self.inited = False

        self.initUi()

    # ----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setRowCount(1)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)

        self.setMaximumHeight(self.sizeHint().height())

    # ----------------------------------------------------------------------
    def updateData(self, data):
        """更新数据"""
        if not self.inited:
            self.setColumnCount(len(data))
            self.setHorizontalHeaderLabels(list(data.keys()))

            col = 0
            for k, v in data.items():
                cell = QtGui.QTableWidgetItem(str(v))
                self.keyCellDict[k] = cell
                self.setItem(0, col, cell)
                col += 1

            self.inited = True
        else:
            for k, v in data.items():
                cell = self.keyCellDict[k]
                cell.setText(str(v))


########################################################################
class CtaStrategyManager(QtGui.QGroupBox):
    """策略管理组件"""
    signal = QtCore.pyqtSignal(type(Event()))

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, name, parent=None):
        """Constructor"""
        super(CtaStrategyManager, self).__init__(parent)

        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        self.name = name

        self.initUi()
        self.updateMonitor()
        self.registerEvent()

    # ----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setTitle(self.name)

        self.paramMonitor = CtaValueMonitor(self)
        self.varMonitor = CtaValueMonitor(self)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(self.paramMonitor)

        hbox3 = QtGui.QHBoxLayout()
        hbox3.addWidget(self.varMonitor)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        self.setLayout(vbox)

    # ----------------------------------------------------------------------
    def updateMonitor(self, event=None):
        """显示策略最新状态"""
        paramDict = self.ctaEngine.getStrategyParam(self.name)
        if paramDict:
            self.paramMonitor.updateData(paramDict)

        varDict = self.ctaEngine.getStrategyVar(self.name)
        if varDict:
            self.varMonitor.updateData(varDict)

    # ----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateMonitor)
        self.eventEngine.register(EVENT_CTA_STRATEGY + self.name, self.signal.emit)


########################################################################
class CtaEngineManager(QtGui.QWidget):
    """CTA引擎管理组件"""
    signal = QtCore.pyqtSignal(type(Event()))

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, parent=None):
        """Constructor"""
        super(CtaEngineManager, self).__init__(parent)

        self.gatewayName = 'CTP'  # gateway对象名称
        self.gateway = VtGateway(eventEngine, self.gatewayName)  # gateway对象

        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine

        self.strategyLoaded = False
        # 初始化界面
        self.initUi()

        # 注册事件监听
        self.registerEvent()

        # 记录日志
        self.ctaEngine.writeCtaLog(CTA_ENGINE_STARTED)

        # 初始化策略
        # 预留几秒时间缓冲
        t.sleep(5)
        while self.strategyLoaded is False:
            self.load()
        else:
            init = self.initAll()
        if init is True:
            self.startAll()

    # ----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(CTA_STRATEGY)

        # 按钮
        startAllButton = QtGui.QPushButton(START_ALL)
        stopAllButton = QtGui.QPushButton(STOP_ALL)
        savePositionButton = QtGui.QPushButton(SAVE_POSITION_DATA)

        startAllButton.clicked.connect(self.startAll)
        stopAllButton.clicked.connect(self.stopAll)
        # savePositionButton.clicked.connect(self.ctaEngine.savePosition)

        # 滚动区域，放置所有的CtaStrategyManager
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)

        # CTA组件的日志监控
        self.ctaLogMonitor = QtGui.QTextEdit()
        self.ctaLogMonitor.setReadOnly(True)
        self.ctaLogMonitor.setMaximumHeight(200)

        # 设置布局
        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(startAllButton)
        hbox2.addWidget(stopAllButton)
        # hbox2.addWidget(savePositionButton)
        hbox2.addStretch()

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox2)
        vbox.addWidget(self.scrollArea)
        vbox.addWidget(self.ctaLogMonitor)
        self.setLayout(vbox)

    # ----------------------------------------------------------------------
    def initStrategyManager(self):
        """初始化策略管理组件界面"""
        w = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        for name in list(self.ctaEngine.strategyDict.keys()):
            strategyManager = CtaStrategyManager(self.ctaEngine, self.eventEngine, name)
            vbox.addWidget(strategyManager)

        vbox.addStretch()

        w.setLayout(vbox)
        self.scrollArea.setWidget(w)

    # ----------------------------------------------------------------------
    def initAll(self):
        """全部初始化"""
        for name in list(self.ctaEngine.strategyDict.keys()):
            self.ctaEngine.initStrategy(name)

        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = u'策略全部初始化'
        self.gateway.onLog(log)
        return True

    # ----------------------------------------------------------------------
    def startAll(self):
        """全部启动"""
        for name in list(self.ctaEngine.strategyDict.keys()):
            self.ctaEngine.startStrategy(name)

        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = u'策略全部启动'
        self.gateway.onLog(log)

    # ----------------------------------------------------------------------
    def stopAll(self):
        """全部停止"""
        for name in list(self.ctaEngine.strategyDict.keys()):
            self.ctaEngine.stopStrategy(name)

        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = u'策略全部停止'
        self.gateway.onLog(log)

    # ----------------------------------------------------------------------
    def load(self):
        """加载策略"""
        if not self.strategyLoaded:
            self.ctaEngine.loadSetting()
            self.initStrategyManager()
            self.strategyLoaded = True
            self.ctaEngine.writeCtaLog(STRATEGY_LOADED)

        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = u'全部策略加载完成'
        self.gateway.onLog(log)

    # ----------------------------------------------------------------------
    def updateCtaLog(self, event):
        """更新CTA相关日志"""
        log = event.dict_['data']
        content = '\t'.join([log.logTime, log.logContent])
        self.ctaLogMonitor.append(content)

    # ----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateCtaLog)
        self.eventEngine.register(EVENT_CTA_LOG, self.signal.emit)
