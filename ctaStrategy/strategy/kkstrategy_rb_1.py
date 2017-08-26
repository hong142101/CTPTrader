# encoding: UTF-8

"""
基于King Keltner通道的交易策略，适合用在股指上，
展示了OCO委托和5分钟K线聚合的方法。

注意事项：
1. 作者不对交易盈利做任何保证，策略代码仅供参考
2. 本策略需要用到talib，没有安装的用户请先参考www.vnpy.org上的教程安装
3. 将IF0000_1min.csv用ctaHistoryData.py导入MongoDB后，直接运行本文件即可回测策略
"""

from __future__ import division

import os
import sys

file_path = os.path.abspath(__file__)
folder_path = os.path.dirname(file_path)
ctastrategy_path = os.path.dirname(folder_path)
root_path = os.path.dirname(ctastrategy_path)
sys.path.append(ctastrategy_path)

from ctaBase import *
from ctaTemplate import CtaTemplate


########################################################################
class kkstrategy_rb_1(CtaTemplate):
    """基于King Keltner通道的交易策略"""
    className = 'kkstrategy_rb_1'
    author = 'sola'
    # 策略变量
    bar = None  # 1分钟K线对象
    barMinute = EMPTY_STRING  # K线当前的分钟点

    buyOrderID = None
    shortOrderID = None
    sellOrderID = None
    coverOrderID = None
    orderList = []  # 保存委托代码的列表

    upperLimit = 999999  # 涨停价
    lowerLimit = 0  # 跌停价

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'long_pos',
               'short_pos']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(kkstrategy_rb_1, self).__init__(ctaEngine, setting)

        self.ctaEngine = ctaEngine

    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' % self.name)

        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar()
        long_pos = self.long_pos
        short_pos = self.short_pos
        for bar in initData:
            if bar.datetime <= self.long_pos_open_datetime:
                self.long_pos = 0
            else:
                self.long_pos = long_pos
            if bar.datetime <= self.short_pos_open_datetime:
                self.short_pos = 0
            else:
                self.short_pos = short_pos
            self.onBar(bar)

        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 聚合为1分钟K线
        tickMinute = tick.datetime.minute

        if tickMinute != self.barMinute:
            if self.bar:
                self.onBar(self.bar)
            self.upperLimit = min(self.upperLimit, tick.upperLimit)
            self.lowerLimit = max(self.lowerLimit, tick.lowerLimit)
            bar = CtaBarData()
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime  # K线的时间设为第一个Tick的时间

            self.bar = bar  # 这种写法为了减少一层访问，加快速度
            self.barMinute = tickMinute  # 更新当前的分钟

        else:  # 否则继续累加新的K线
            bar = self.bar  # 写法同样为了加快速度

            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
        for orderID in self.orderList:
            self.cancelOrder(orderID)
        self.orderList = []
        
        # 当前无仓位
        if self.long_pos == 0 and self.short_pos == 0:
            self.buyOrderID = self.buy(self.upperLimit, 1, False)
        elif self.long_pos != 0 and self.short_pos == 0:
            self.shortOrderID = self.short(self.lowerLimit, 1, False)
        elif self.long_pos != 0 and self.short_pos != 0:
            self.sellOrderID = self.sell(self.lowerLimit, 1, False)
        elif self.long_pos == 0 and self.short_pos != 0:
            self.coverOrderID = self.cover(self.upperLimit, 1, False)
        
        self.orderList.append(self.buyOrderID)
        self.orderList.append(self.shortOrderID)
        # 发出状态更新事件
        self.putEvent()
        pass

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        # print(order.__dict__)

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        # 多头开仓成交后，撤消空头委托
        # print(trade.__dict__)

        if (trade.offset == "开仓") and (trade.direction == "多"):
            if self.buyOrderID in self.orderList:
                self.orderList.remove(self.buyOrderID)

        if ("平" in trade.offset) and (trade.direction == "空"):
            if self.sellOrderID in self.orderList:
                self.orderList.remove(self.sellOrderID)

        if (trade.offset == "开仓") and (trade.direction == "空"):
            if self.shortOrderID in self.orderList:
                self.orderList.remove(self.shortOrderID)

        if ("平" in trade.offset) and (trade.direction == "多"):
            if self.coverOrderID in self.orderList:
                self.orderList.remove(self.coverOrderID)

        self.updatePosition(self.className, trade)

        # 发出状态更新事件
        self.putEvent()


# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # 提供直接双击回测的功能
    # 导入PyQt4的包是为了保证matplotlib使用PyQt4而不是PySide，防止初始化出错
    from ctaBacktesting import *
    from PyQt4 import QtCore, QtGui

    # 创建回测引擎
    engine = BacktestingEngine()

    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20110101')
    symbol = 'rb0000'

    # 设置产品相关参数
    engine.setSlippage(2)  # 股指1跳
    engine.setRate(1.2 / 10000)  # 万0.3
    engine.setSize(10)  # 股指合约大小
    engine.setPriceTick(1)  # 股指最小价格变动

    # 设置使用的历史数据库
    engine.setDatabase(MINUTE_DB_NAME, symbol)

    # 在引擎中创建策略对象
    d = {}
    engine.initStrategy(kkstrategy_rb_1, d)

    # 开始跑回测
    engine.runBacktesting(symbol)

    # 显示回测结果
    engine.showBacktestingResult()
