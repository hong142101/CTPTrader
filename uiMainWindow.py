# encoding: UTF-8

import time as t
import psutil

from ctpGateway.ctpGateway import CtpGateway
from uiBasicWidget import *
from ctaStrategy.uiCtaWidget import CtaEngineManager


########################################################################
class MainWindow(QtGui.QMainWindow):
    """主窗口"""
    signalStatusBar = QtCore.pyqtSignal(type(Event()))

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        super(MainWindow, self).__init__()

        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        self.widgetDict = {}  # 用来保存子窗口的字典
        self.init_status_bar = False

        self.initUi()
        self.loadWindowSettings('custom')

        # 连接CTP接口
        self.mainEngine.connect()
        # 初始化策略界面
        while (self.init_status_bar is False) or (self.mainEngine.ctp_get_all_contract is False):
            print(self.init_status_bar, self.mainEngine.ctp_get_all_contract)
            t.sleep(1)
        else:
            self.openCta()

    # ----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle('CTPTrader')
        self.initCentral()
        self.initMenu()
        self.initStatusBar()

    # ----------------------------------------------------------------------
    def initCentral(self):
        """初始化中心区域"""
        widgetTradeM, dockTradeM = self.createDock(TradeMonitor, TRADE, QtCore.Qt.TopDockWidgetArea)
        widgetOrderM, dockOrderM = self.createDock(OrderMonitor, ORDER, QtCore.Qt.TopDockWidgetArea)
        widgetLogM, dockLogM = self.createDock(LogMonitor, LOG, QtCore.Qt.BottomDockWidgetArea)
        widgetErrorM, dockErrorM = self.createDock(ErrorMonitor, ERROR, QtCore.Qt.BottomDockWidgetArea)
        widgetPositionM, dockPositionM = self.createDock(PositionMonitor, POSITION, QtCore.Qt.BottomDockWidgetArea)
        widgetTradingM, dockAccountM = self.createDock(AccountMonitor, ACCOUNT, QtCore.Qt.BottomDockWidgetArea)

        # 保存默认设置
        self.saveWindowSettings('default')

    # ----------------------------------------------------------------------
    def initMenu(self):
        """初始化菜单"""
        # 创建菜单
        menubar = self.menuBar()

        # 设计为只显示存在的接口
        sysMenu = menubar.addMenu(SYSTEM)

        sysMenu.addSeparator()
        sysMenu.addAction(self.createAction(EXIT, self.close))

        # 算法相关
        strategyMenu = menubar.addMenu(STRATEGY)
        strategyMenu.addAction(self.createAction(CTA_STRATEGY, self.openCta))

        # 帮助
        helpMenu = menubar.addMenu(HELP)
        helpMenu.addAction(self.createAction(RESTORE, self.restoreWindow))

    # ----------------------------------------------------------------------
    def initStatusBar(self):
        """初始化状态栏"""
        self.statusLabel = QtGui.QLabel()
        self.statusLabel.setAlignment(QtCore.Qt.AlignLeft)

        self.statusBar().addPermanentWidget(self.statusLabel)
        self.statusLabel.setText(self.getCpuMemory())

        self.sbCount = 0
        self.sbTrigger = 5  # 5秒刷新一次
        self.signalStatusBar.connect(self.updateStatusBar)
        self.eventEngine.register(EVENT_TIMER, self.signalStatusBar.emit)

        self.init_status_bar = True

    # ----------------------------------------------------------------------
    def updateStatusBar(self, event):
        """在状态栏更新CPU和内存信息"""
        self.sbCount += 1

        if self.sbCount == self.sbTrigger:
            self.sbCount = 0
            self.statusLabel.setText(self.getCpuMemory())

    # ----------------------------------------------------------------------
    def getCpuMemory(self):
        """获取CPU和内存状态信息"""
        cpuPercent = psutil.cpu_percent()
        memoryPercent = psutil.virtual_memory().percent
        return CPU_MEMORY_INFO.format(cpu=cpuPercent, memory=memoryPercent)

    # ----------------------------------------------------------------------
    def createAction(self, actionName, function):
        """创建操作功能"""
        action = QtGui.QAction(actionName, self)
        action.triggered.connect(function)
        return action

    # ----------------------------------------------------------------------
    def test(self):
        """测试按钮用的函数"""
        # 有需要使用手动触发的测试函数可以写在这里
        pass

    # ----------------------------------------------------------------------
    def openCta(self):
        """打开CTA组件"""
        try:
            self.widgetDict['ctaM'].showMaximized()
        except KeyError:
            self.widgetDict['ctaM'] = CtaEngineManager(self.mainEngine.ctaEngine, self.eventEngine)
            self.widgetDict['ctaM'].showMaximized()

    # ----------------------------------------------------------------------
    def closeEvent(self, event):
        """关闭事件"""
        reply = QtGui.QMessageBox.question(self, EXIT,
                                           CONFIRM_EXIT, QtGui.QMessageBox.Yes |
                                           QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            for widget in list(self.widgetDict.values()):
                widget.close()
            self.saveWindowSettings('custom')

            self.mainEngine.exit()
            event.accept()
        else:
            event.ignore()

    # ----------------------------------------------------------------------
    def createDock(self, widgetClass, widgetName, widgetArea):
        """创建停靠组件"""
        widget = widgetClass(self.mainEngine, self.eventEngine)
        dock = QtGui.QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        dock.setFeatures(dock.DockWidgetFloatable | dock.DockWidgetMovable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock

    # ----------------------------------------------------------------------
    def saveWindowSettings(self, settingName):
        """保存窗口设置"""
        settings = QtCore.QSettings('vn.trader', settingName)
        settings.setValue('state', self.saveState())
        settings.setValue('geometry', self.saveGeometry())

    # ----------------------------------------------------------------------
    def loadWindowSettings(self, settingName):
        """载入窗口设置"""
        settings = QtCore.QSettings('vn.trader', settingName)
        # 这里由于PyQt4的版本不同，settings.value('state')调用返回的结果可能是：
        # 1. None（初次调用，注册表里无相应记录，因此为空）
        # 2. QByteArray（比较新的PyQt4）
        # 3. QVariant（以下代码正确执行所需的返回结果）
        # 所以为了兼容考虑，这里加了一个try...except，如果是1、2的情况就pass
        # 可能导致主界面的设置无法载入（每次退出时的保存其实是成功了）
        try:
            self.restoreState(settings.value('state').toByteArray())
            self.restoreGeometry(settings.value('geometry').toByteArray())
        except AttributeError:
            pass

    # ----------------------------------------------------------------------
    def restoreWindow(self):
        """还原默认窗口设置（还原停靠组件位置）"""
        self.loadWindowSettings('default')
        self.showMaximized()

