# encoding: UTF-8

""""
本文件中包含的是CTA模块的回测引擎，回测引擎的API和CTA引擎一致，
可以使用和实盘相同的代码进行回测。
"""

from __future__ import division

import sys

import csv
from datetime import datetime, timedelta
from collections import OrderedDict
from itertools import product
import multiprocessing

from ctaBase import *
from strategy import *

from vtGateway import *

file_path = os.path.abspath(__file__)
folder_path = os.path.dirname(file_path)
root_path = os.path.dirname(folder_path)
globalresultList = []


########################################################################
class BacktestingEngine(object):
    """
    CTA回测引擎
    函数接口和策略引擎保持一样，
    从而实现同一套代码从回测到实盘。
    """

    TICK_MODE = 'tick'
    BAR_MODE = 'bar'

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        # 本地停止单编号计数
        self.stopOrderCount = 0
        # stopOrderID = STOPORDERPREFIX + str(stopOrderCount)

        # 本地停止单字典
        # key为stopOrderID，value为stopOrder对象
        self.stopOrderDict = {}  # 停止单撤销后不会从本字典中删除
        self.workingStopOrderDict = {}  # 停止单撤销后会从本字典中删除

        # 引擎类型为回测
        self.engineType = ENGINETYPE_BACKTESTING

        # 回测相关
        self.strategy = None  # 回测策略
        self.mode = self.BAR_MODE  # 回测模式，默认为K线
        self.long_pos = 0  # 用于合约换月的持仓初始化
        self.short_pos = 0  # 用于合约换月的持仓初始化

        self.startDate = ''
        self.initDays = 0
        self.endDate = ''

        self.slippage = 0  # 回测时假设的滑点
        self.rate = 0  # 回测时假设的佣金比例（适用于百分比佣金）
        self.size = 1  # 合约大小，默认为1
        self.priceTick = 0  # 价格最小变动

        self.dbClient = None  # 数据库客户端
        self.dbCursor = None  # 数据库指针

        # self.historyData = []       # 历史数据的列表，回测用
        self.initData = []  # 初始化用的数据
        # self.backtestingData = []   # 回测用的数据

        self.dataStartDate = None  # 回测数据开始日期，datetime对象
        self.dataEndDate = None  # 回测数据结束日期，datetime对象
        self.strategyStartDate = None  # 策略启动日期（即前面的数据用于初始化），datetime对象

        self.limitOrderDict = OrderedDict()  # 限价单字典
        self.workingLimitOrderDict = OrderedDict()  # 活动限价单字典，用于进行撮合用
        self.limitOrderCount = 0  # 限价单编号

        self.tradeCount = 0  # 成交编号
        self.tradeDict = OrderedDict()  # 成交字典
        self.resultList = []  # 交易结果列表

        self.logList = []  # 日志记录

        # 当前最新数据，用于模拟成交用
        self.tick = None
        self.bar = None
        self.dt = None  # 最新的时间

    # ----------------------------------------------------------------------
    def setStartDate(self, startDate='20100416', initDays=10):
        """设置回测的启动日期"""
        self.startDate = startDate
        self.initDays = initDays

        self.dataStartDate = datetime.strptime(startDate, '%Y%m%d')

        initTimeDelta = timedelta(initDays)
        self.strategyStartDate = self.dataStartDate + initTimeDelta

    # ----------------------------------------------------------------------
    def setEndDate(self, endDate=''):
        """设置回测的结束日期"""
        self.endDate = endDate
        if endDate:
            self.dataEndDate = datetime.strptime(endDate, '%Y%m%d')
            # 若不修改时间则会导致不包含dataEndDate当天数据
            self.dataEndDate.replace(hour=23, minute=59)

    # ----------------------------------------------------------------------
    def setBacktestingMode(self, mode):
        """设置回测模式"""
        self.mode = mode

    # ----------------------------------------------------------------------
    def convertDictType(self, data):
        # 将读出来的数据字典中的数据的格式做强制转换

        data['open'] = float(data['open'])
        data['vtSymbol'] = str(data['vtSymbol'])
        data['symbol'] = str(data['symbol'])
        data['exchange'] = str(data['exchange'])
        data['datetime'] = datetime.strptime(data['datetime'], '%Y-%m-%d %H:%M:%S')
        data['date'] = str(data['date'])
        data['time'] = str(data['time'])
        data['open'] = float(data['open'])
        data['high'] = float(data['high'])
        data['low'] = float(data['low'])
        data['close'] = float(data['close'])
        data['volume'] = int(data['volume'])
        data['openInterest'] = int(data['openInterest'])

        return data

    # ----------------------------------------------------------------------
    def runBacktesting(self, filename):
        """运行回测"""
        # 载入历史数据
        history_data_path = os.path.join(root_path, "history_data")
        history_data_file = os.path.join(history_data_path, filename + ".csv")
        file = open(history_data_file, 'r')
        lines = csv.DictReader(file)

        # 首先根据回测模式，确认要使用的数据类
        if self.mode == self.BAR_MODE:
            dataClass = CtaBarData
            func = self.newBar
        else:
            dataClass = CtaTickData
            func = self.newTick

        # self.output(u'开始回测')

        self.strategy.inited = True
        self.strategy.onInit()
        # self.output(u'策略初始化完成')

        self.strategy.trading = True
        self.strategy.onStart()
        # self.output(u'策略启动完成')

        # self.output(u'开始回放数据')

        for d in lines:
            if d['datetime'] <= str(self.strategyStartDate):
                continue
            data = dataClass()
            datadict = self.convertDictType(d)
            data.__dict__ = datadict
            func(data)

            # self.output(u'数据回放结束')

    # ----------------------------------------------------------------------
    def newBar(self, bar):
        """新的K线"""
        # 考虑到换月的需求，会在期货合约号发生变动的时候强制在最后一根的close平仓，并在新的bar开仓
        if self.bar:
            # print(self.bar.__dict__)
            # print(bar.__dict__)
            if self.bar.vtSymbol != bar.vtSymbol:
                self.long_pos = self.strategy.long_pos
                self.short_pos = self.strategy.short_pos
                if self.strategy.long_pos:
                    self.strategy.sell(0, abs(self.strategy.long_pos), stop=False)
                if self.strategy.short_pos:
                    self.strategy.cover(999999, abs(self.strategy.short_pos), stop=False)
                self.crossLimitOrder()  # 先撮合限价单
                self.crossStopOrder()  # 再撮合停止单

        self.bar = bar
        self.dt = bar.datetime
        if self.long_pos:
            self.strategy.buy(999999, abs(self.long_pos), stop=False)
            self.long_pos = 0
        if self.short_pos:
            self.strategy.short(0, abs(self.short_pos), stop=False)
            self.short_pos = 0
        self.crossLimitOrder()  # 先撮合限价单
        self.crossStopOrder()  # 再撮合停止单
        self.strategy.onBar(bar)  # 推送K线到策略中

    # ----------------------------------------------------------------------
    def newTick(self, tick):
        """新的Tick"""
        if self.tick:
            # print(self.bar.__dict__)
            # print(bar.__dict__)
            if self.tick.vtSymbol != tick.vtSymbol:
                self.long_pos = self.strategy.long_pos
                self.short_pos = self.strategy.short_pos
                if self.strategy.long_pos:
                    self.strategy.sell(0, abs(self.strategy.long_pos), stop=False)
                if self.strategy.short_pos:
                    self.strategy.cover(999999, abs(self.strategy.short_pos), stop=False)
                self.crossLimitOrder()  # 先撮合限价单
                self.crossStopOrder()  # 再撮合停止单

        self.tick = tick
        self.dt = tick.datetime
        if self.long_pos:
            self.strategy.buy(999999, abs(self.long_pos), stop=False)
            self.long_pos = 0
        if self.short_pos:
            self.strategy.short(0, abs(self.short_pos), stop=False)
            self.short_pos = 0
        self.crossLimitOrder()
        self.crossStopOrder()
        self.strategy.onTick(tick)

    # ----------------------------------------------------------------------
    def initStrategy(self, strategyClass, setting=None):
        """
        初始化策略
        setting是策略的参数设置，如果使用类中写好的默认设置则可以不传该参数
        """
        self.setStartDate()
        self.strategy = strategyClass(self, setting)
        self.strategy.name = self.strategy.className

    # ----------------------------------------------------------------------
    def sendOrder(self, vtSymbol, orderType, price, volume, strategy):
        """发单"""
        self.limitOrderCount += 1
        orderID = str(self.limitOrderCount)

        order = VtOrderData()
        order.vtSymbol = vtSymbol
        order.price = self.roundToPrickTick(price)
        order.totalVolume = volume
        order.status = STATUS_NOTTRADED  # 刚提交尚未成交
        order.orderID = orderID
        order.vtOrderID = orderID
        order.orderTime = str(self.dt)

        # CTA委托类型映射
        if orderType == CTAORDER_BUY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_SELL:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSE
        elif orderType == CTAORDER_SHORT:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_COVER:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSE

            # 保存到限价单字典中
        self.workingLimitOrderDict[orderID] = order
        self.limitOrderDict[orderID] = order

        return orderID

    # ----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """撤单"""
        if vtOrderID in self.workingLimitOrderDict:
            order = self.workingLimitOrderDict[vtOrderID]
            order.status = STATUS_CANCELLED
            order.cancelTime = str(self.dt)
            del self.workingLimitOrderDict[vtOrderID]

    # ----------------------------------------------------------------------
    def sendStopOrder(self, vtSymbol, orderType, price, volume, strategy):
        """发停止单（本地实现）"""
        self.stopOrderCount += 1
        stopOrderID = STOPORDERPREFIX + str(self.stopOrderCount)

        so = StopOrder()
        so.vtSymbol = vtSymbol
        so.price = self.roundToPrickTick(price)
        so.volume = volume
        so.strategy = strategy
        so.stopOrderID = stopOrderID
        so.status = STOPORDER_WAITING

        if orderType == CTAORDER_BUY:
            so.direction = DIRECTION_LONG
            so.offset = OFFSET_OPEN
        elif orderType == CTAORDER_SELL:
            so.direction = DIRECTION_SHORT
            so.offset = OFFSET_CLOSE
        elif orderType == CTAORDER_SHORT:
            so.direction = DIRECTION_SHORT
            so.offset = OFFSET_OPEN
        elif orderType == CTAORDER_COVER:
            so.direction = DIRECTION_LONG
            so.offset = OFFSET_CLOSE

            # 保存stopOrder对象到字典中
        self.stopOrderDict[stopOrderID] = so
        self.workingStopOrderDict[stopOrderID] = so

        return stopOrderID

    # ----------------------------------------------------------------------
    def cancelStopOrder(self, stopOrderID):
        """撤销停止单"""
        # 检查停止单是否存在
        if stopOrderID in self.workingStopOrderDict:
            so = self.workingStopOrderDict[stopOrderID]
            so.status = STOPORDER_CANCELLED
            del self.workingStopOrderDict[stopOrderID]

    # ----------------------------------------------------------------------
    def crossLimitOrder(self):
        """基于最新数据撮合限价单"""
        # 先确定会撮合成交的价格
        if self.mode == self.BAR_MODE:
            buyCrossPrice = self.bar.low  # 若买入方向限价单价格高于该价格，则会成交
            sellCrossPrice = self.bar.high  # 若卖出方向限价单价格低于该价格，则会成交
            buyBestCrossPrice = self.bar.open  # 在当前时间点前发出的买入委托可能的最优成交价
            sellBestCrossPrice = self.bar.open  # 在当前时间点前发出的卖出委托可能的最优成交价
        else:
            buyCrossPrice = self.tick.askPrice1
            sellCrossPrice = self.tick.bidPrice1
            buyBestCrossPrice = self.tick.askPrice1
            sellBestCrossPrice = self.tick.bidPrice1

        # 遍历限价单字典中的所有限价单
        for orderID, order in self.workingLimitOrderDict.items():
            # 判断是否会成交
            buyCross = order.direction == DIRECTION_LONG and order.price >= buyCrossPrice
            sellCross = order.direction == DIRECTION_SHORT and order.price <= sellCrossPrice

            # 如果发生了成交
            if buyCross or sellCross:
                # 推送成交数据
                self.tradeCount += 1  # 成交编号自增1
                tradeID = str(self.tradeCount)
                trade = VtTradeData()
                trade.vtSymbol = order.vtSymbol
                trade.tradeID = tradeID
                trade.vtTradeID = tradeID
                trade.orderID = order.orderID
                trade.vtOrderID = order.orderID
                trade.direction = order.direction
                trade.offset = order.offset

                # 以买入为例：
                # 1. 假设当根K线的OHLC分别为：100, 125, 90, 110
                # 2. 假设在上一根K线结束(也是当前K线开始)的时刻，策略发出的委托为限价105
                # 3. 则在实际中的成交价会是100而不是105，因为委托发出时市场的最优价格是100
                if buyCross:
                    trade.price = min(order.price, buyBestCrossPrice)
                    self.strategy.pos += order.totalVolume
                else:
                    trade.price = max(order.price, sellBestCrossPrice)
                    self.strategy.pos -= order.totalVolume

                trade.volume = order.totalVolume
                trade.tradeTime = str(self.dt)
                trade.dt = self.dt
                self.strategy.onTrade(trade)

                self.tradeDict[tradeID] = trade

                # 推送委托数据
                order.tradedVolume = order.totalVolume
                order.status = STATUS_ALLTRADED
                self.strategy.onOrder(order)

                # 从字典中删除该限价单
                del self.workingLimitOrderDict[orderID]

    # ----------------------------------------------------------------------
    def crossStopOrder(self):
        """基于最新数据撮合停止单"""
        # 先确定会撮合成交的价格，这里和限价单规则相反
        if self.mode == self.BAR_MODE:
            buyCrossPrice = self.bar.high  # 若买入方向停止单价格低于该价格，则会成交
            sellCrossPrice = self.bar.low  # 若卖出方向限价单价格高于该价格，则会成交
            bestCrossPrice = self.bar.open  # 最优成交价，买入停止单不能低于，卖出停止单不能高于
        else:
            buyCrossPrice = self.tick.lastPrice
            sellCrossPrice = self.tick.lastPrice
            bestCrossPrice = self.tick.lastPrice

        # 遍历停止单字典中的所有停止单
        for stopOrderID, so in list(self.workingStopOrderDict.items()):
            # 判断是否会成交
            buyCross = so.direction == DIRECTION_LONG and so.price <= buyCrossPrice
            sellCross = so.direction == DIRECTION_SHORT and so.price >= sellCrossPrice

            # 如果发生了成交
            if buyCross or sellCross:
                # 推送成交数据
                self.tradeCount += 1  # 成交编号自增1
                tradeID = str(self.tradeCount)
                trade = VtTradeData()
                trade.vtSymbol = so.vtSymbol
                trade.tradeID = tradeID
                trade.vtTradeID = tradeID
                """
                还需要判断成交的开平仓来确定对多空仓位的操作
                """
                if buyCross:
                    if '开' in so.offset:
                        self.strategy.long_pos += so.volume
                    elif '平' in so.offset:
                        self.strategy.short_pos += so.volume
                    self.strategy.pos += so.volume
                    trade.price = max(bestCrossPrice, so.price)
                else:
                    if '开' in so.offset:
                        self.strategy.short_pos -= so.volume
                    elif '平' in so.offset:
                        self.strategy.long_pos -= so.volume
                    self.strategy.pos -= so.volume
                    trade.price = min(bestCrossPrice, so.price)

                self.limitOrderCount += 1
                orderID = str(self.limitOrderCount)
                trade.orderID = orderID
                trade.vtOrderID = orderID

                trade.direction = so.direction
                trade.offset = so.offset
                trade.volume = so.volume
                trade.tradeTime = str(self.dt)
                trade.dt = self.dt
                self.strategy.onTrade(trade)

                self.tradeDict[tradeID] = trade

                # 推送委托数据
                so.status = STOPORDER_TRIGGERED

                order = VtOrderData()
                order.vtSymbol = so.vtSymbol
                order.symbol = so.vtSymbol
                order.orderID = orderID
                order.vtOrderID = orderID
                order.direction = so.direction
                order.offset = so.offset
                order.price = so.price
                order.totalVolume = so.volume
                order.tradedVolume = so.volume
                order.status = STATUS_ALLTRADED
                order.orderTime = trade.tradeTime
                self.strategy.onOrder(order)

                self.limitOrderDict[orderID] = order

                # 从字典中删除该限价单
                if stopOrderID in self.workingStopOrderDict:
                    del self.workingStopOrderDict[stopOrderID]

    # ----------------------------------------------------------------------
    def insertData(self, dbName, collectionName, data):
        """考虑到回测中不允许向数据库插入数据，防止实盘交易中的一些代码出错"""
        pass

    # ----------------------------------------------------------------------
    def loadBar(self, dbName, collectionName, startDate):
        """直接返回初始化数据列表中的Bar"""
        return self.initData

    # ----------------------------------------------------------------------
    def loadTick(self, dbName, collectionName, startDate):
        """直接返回初始化数据列表中的Tick"""
        return self.initData

    # ----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """记录日志"""
        log = str(self.dt) + ' ' + content
        self.logList.append(log)

    # ----------------------------------------------------------------------
    def calculateBacktestingResult(self):
        """
        计算回测结果
        """
        # self.output(u'计算回测结果')

        # 首先基于回测后的成交记录，计算每笔交易的盈亏
        longTrade = []  # 未平仓的多头交易
        shortTrade = []  # 未平仓的空头交易

        for trade in list(self.tradeDict.values()):
            # 多头交易
            if trade.direction == DIRECTION_LONG:
                # 如果尚无空头交易
                if not shortTrade:
                    longTrade.append(trade)
                # 当前多头交易为平空
                else:
                    while True:
                        entryTrade = shortTrade[0]
                        exitTrade = trade

                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dt,
                                               exitTrade.price, exitTrade.dt,
                                               -closedVolume, self.rate, self.slippage, self.size)
                        globalresultList.append(result)

                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume

                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            shortTrade.pop(0)

                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break

                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not shortTrade:
                                longTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass

            # 空头交易        
            else:
                # 如果尚无多头交易
                if not longTrade:
                    shortTrade.append(trade)
                # 当前空头交易为平多
                else:
                    while True:
                        entryTrade = longTrade[0]
                        exitTrade = trade

                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dt,
                                               exitTrade.price, exitTrade.dt,
                                               closedVolume, self.rate, self.slippage, self.size)
                        globalresultList.append(result)

                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume

                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            longTrade.pop(0)

                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break

                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not longTrade:
                                shortTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass

        # 检查是否有交易
        if not globalresultList:
            logging.info(u'无交易结果')
            return False
        else:
            return True

    # ------------------------------------------------------------------------------
    def calculateBacktestingResultIndex(self):
        """计算组合策略的交易结果的各个指标值"""
        resultList = []
        for result in globalresultList:
            resultList.append(result.__dict__)
        resultList.sort(key=lambda x: x['exitDt'])
        # 然后基于每笔交易的结果，我们可以计算具体的盈亏曲线和最大回撤等        
        capital = 0  # 资金
        maxCapital = 0  # 资金最高净值
        drawdown = 0  # 回撤

        totalResult = 0  # 总成交数量
        totalTurnover = 0  # 总成交金额（合约面值）
        totalCommission = 0  # 总手续费
        totalSlippage = 0  # 总滑点

        timeList = []  # 时间序列
        pnlList = []  # 每笔盈亏序列
        capitalList = []  # 盈亏汇总的时间序列
        drawdownList = []  # 回撤的时间序列

        winningResult = 0  # 盈利次数
        losingResult = 0  # 亏损次数
        totalWinning = 0  # 总盈利金额
        totalLosing = 0  # 总亏损金额

        for result in resultList:
            # print(result)
            capital += result['pnl']
            maxCapital = max(capital, maxCapital)
            drawdown = capital - maxCapital

            pnlList.append(result['pnl'])
            timeList.append(result['exitDt'])  # 交易的时间戳使用平仓时间
            capitalList.append(capital)
            drawdownList.append(drawdown)

            totalResult += 1
            totalTurnover += result['turnover']
            totalCommission += result['commission']
            totalSlippage += result['slippage']

            if result['pnl'] >= 0:
                winningResult += 1
                totalWinning += result['pnl']
            else:
                losingResult += 1
                totalLosing += result['pnl']

        # 计算盈亏相关数据
        winningRate = winningResult / totalResult * 100  # 胜率

        averageWinning = 0  # 这里把数据都初始化为0
        averageLosing = 0
        profitLossRatio = 0

        if winningResult:
            averageWinning = totalWinning / winningResult  # 平均每笔盈利
        if losingResult:
            averageLosing = totalLosing / losingResult  # 平均每笔亏损
        if averageLosing:
            profitLossRatio = -averageWinning / averageLosing  # 盈亏比

        # 返回回测结果
        d = {}
        d['capital'] = capital
        d['maxCapital'] = maxCapital
        d['drawdown'] = drawdown
        d['totalResult'] = totalResult
        d['totalTurnover'] = totalTurnover
        d['totalCommission'] = totalCommission
        d['totalSlippage'] = totalSlippage
        d['timeList'] = timeList
        d['pnlList'] = pnlList
        d['capitalList'] = capitalList
        d['drawdownList'] = drawdownList
        d['winningRate'] = winningRate
        d['averageWinning'] = averageWinning
        d['averageLosing'] = averageLosing
        d['profitLossRatio'] = profitLossRatio

        return d

    # ----------------------------------------------------------------------
    def showBacktestingResult(self, d):
        """显示回测结果"""
        # if not (d['capital'] / (-1 * min(d['drawdownList']))) >= 6:
        #     return False
        # 输出
        logging.info('-' * 50)
        logging.info(u'第一笔交易：\t%s' % d['timeList'][0])
        logging.info(u'最后一笔交易：\t%s' % d['timeList'][-1])

        logging.info(u'总交易次数：\t%s' % formatNumber(d['totalResult']))
        logging.info(u'总盈亏：\t%s' % formatNumber(d['capital']))
        logging.info(u'最大回撤: \t%s' % formatNumber(min(d['drawdownList'])))

        logging.info(u'平均每笔盈利：\t%s' % formatNumber(d['capital'] / d['totalResult']))
        logging.info(u'平均每笔滑点：\t%s' % formatNumber(d['totalSlippage'] / d['totalResult']))
        logging.info(u'平均每笔佣金：\t%s' % formatNumber(d['totalCommission'] / d['totalResult']))

        logging.info(u'胜率\t\t%s%%' % formatNumber(d['winningRate']))
        logging.info(u'盈利交易平均值\t%s' % formatNumber(d['averageWinning']))
        logging.info(u'亏损交易平均值\t%s' % formatNumber(d['averageLosing']))
        logging.info(u'盈亏比：\t%s' % formatNumber(d['profitLossRatio']))
        logging.info('-' * 50)

    # ----------------------------------------------------------------------
    def plotBacktestingResult(self, d):
        """
        绘制回测曲线图
        :param d:
        :return:
        """
        import matplotlib.pyplot as plt

        pCapital = plt.subplot(3, 1, 1)
        pCapital.set_ylabel("capital")
        pCapital.plot(d['capitalList'])

        pDD = plt.subplot(3, 1, 2)
        pDD.set_ylabel("DD")
        pDD.bar(range(len(d['drawdownList'])), d['drawdownList'])

        pPnl = plt.subplot(3, 1, 3)
        pPnl.set_ylabel("pnl")
        pPnl.hist(d['pnlList'], bins=50)

        plt.show()

    # ----------------------------------------------------------------------
    def putStrategyEvent(self, name):
        """发送策略更新事件，回测中忽略"""
        pass

    # ----------------------------------------------------------------------
    def setSlippage(self, slippage):
        """设置滑点点数"""
        self.slippage = slippage

    # ----------------------------------------------------------------------
    def setSize(self, size):
        """设置合约大小"""
        self.size = size

    # ----------------------------------------------------------------------
    def setRate(self, rate):
        """设置佣金比例"""
        self.rate = rate

    # ----------------------------------------------------------------------
    def setPriceTick(self, priceTick):
        """设置价格最小变动"""
        self.priceTick = priceTick

    # ----------------------------------------------------------------------
    def clearBacktestingResult(self):
        """清空之前回测的结果"""
        # 清空限价单相关
        self.limitOrderCount = 0
        self.limitOrderDict.clear()
        self.workingLimitOrderDict.clear()

        # 清空停止单相关
        self.stopOrderCount = 0
        self.stopOrderDict.clear()
        self.workingStopOrderDict.clear()

        # 清空成交相关
        self.tradeCount = 0
        self.tradeDict.clear()

    # ----------------------------------------------------------------------
    def roundToPrickTick(self, price):
        """取整价格到合约最小价格变动"""
        if not self.priceTick:
            return price

        newPrice = round(price / self.priceTick, 0) * self.priceTick
        return newPrice


########################################################################
class TradingResult(object):
    """每笔交易的结果"""

    # ----------------------------------------------------------------------
    def __init__(self, entryPrice, entryDt, exitPrice,
                 exitDt, volume, rate, slippage, size):
        """Constructor"""
        self.entryPrice = entryPrice  # 开仓价格
        self.exitPrice = exitPrice  # 平仓价格

        self.entryDt = entryDt  # 开仓时间datetime
        self.exitDt = exitDt  # 平仓时间

        self.volume = volume  # 交易数量（+/-代表方向）

        self.turnover = (self.entryPrice + self.exitPrice) * size * abs(volume)  # 成交金额
        self.commission = self.turnover * rate  # 手续费成本
        self.slippage = slippage * 2 * size * abs(volume)  # 滑点成本
        self.pnl = ((self.exitPrice - self.entryPrice) * volume * size
                    - self.commission - self.slippage)  # 净盈亏


# ----------------------------------------------------------------------
def formatNumber(n):
    """格式化数字到字符串"""
    rn = round(n, 2)  # 保留两位小数
    return format(rn, ',')  # 加上千分符


# ----------------------------------------------------------------------
def setting_to_parameter_groups_dict(setting):
    # 合成用于调整类的参数值的字典
    parameter = []
    for key in setting.keys():
        key_value = setting[key]
        parameter.append(key_value)
    parameter_groups = list(itertools.product(*parameter))

    parameter_groups_dict = []
    for parameter_group in parameter_groups:
        d = dict()
        for i, key in enumerate(setting.keys()):
            d[key] = parameter_group[i]
        parameter_groups_dict.append(d)
    return parameter_groups_dict


# ----------------------------------------------------------------------
def combination_strategy_ctabacktesting(setting, strategy, symbol):
    """
    用于单策略多参数组在单品种的组合回测
    :param setting: 参数组字典
    :param strategy: 单策略类
    :param symbol: 回测合约
    :return:
    """
    # ---------------------------------------------
    # 回测部分
    for d in setting:
        logging.info(d)
        stg = strategy
        # 创建回测引擎
        engine = BacktestingEngine()
        # 设置引擎的回测模式为K线
        engine.setBacktestingMode(engine.BAR_MODE)

        # 设置产品相关参数
        engine.setSlippage(2)  # 股指1跳
        engine.setRate(1.2 / 10000)  # 万0.3
        engine.setSize(10)  # 股指合约大小

        # 在引擎中创建策略对象，跑回测，计算回测结果
        engine.initStrategy(stg, d)
        engine.runBacktesting(symbol)
        engine.calculateBacktestingResult()
    # ---------------------------------------------

    # 显示回测结果
    # spyder或者ipython notebook中运行时，会弹出盈亏曲线图
    # 直接在cmd中回测则只会打印一些回测数值
    result_d = BacktestingEngine().calculateBacktestingResultIndex()
    BacktestingEngine().showBacktestingResult(result_d)
    BacktestingEngine().plotBacktestingResult(result_d)


# ----------------------------------------------------------------------
def all_combination_strategy_ctabacktesting(setting, strategy, symbol):
    """
    用于单策略在单品种上的参数空间全遍历
    :param setting: 参数组字典
    :param strategy: 单策略类
    :param symbol: 回测合约
    :return:
    """
    # ---------------------------------------------
    # 回测部分
    for d in setting:
        logging.info(d)
        stg = strategy
        # 创建回测引擎
        engine = BacktestingEngine()
        # 设置引擎的回测模式为K线
        engine.setBacktestingMode(engine.BAR_MODE)

        # 设置产品相关参数
        engine.setSlippage(2)  # 股指1跳
        engine.setRate(1.2 / 10000)  # 万0.3
        engine.setSize(10)  # 股指合约大小

        # 在引擎中创建策略对象，跑回测，计算回测结果
        engine.initStrategy(stg, d)
        engine.runBacktesting(symbol)
        if engine.calculateBacktestingResult():
            # 显示回测结果
            # spyder或者ipython notebook中运行时，会弹出盈亏曲线图
            # 直接在cmd中回测则只会打印一些回测数值
            result_d = BacktestingEngine().calculateBacktestingResultIndex()
            BacktestingEngine().showBacktestingResult(result_d)
            global globalresultList
            globalresultList = []
            # ---------------------------------------------


########################################################################################################################
if __name__ == '__main__':
    # 以下内容是一段回测脚本的演示，用户可以根据自己的需求修改
    # 建议使用ipython notebook或者spyder来做回测
    # 同样可以在命令模式下进行回测（一行一行输入运行）
    from strategy.kkstrategy_rb_1 import kkstrategy_rb_1 as strategy
    import itertools
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s --<%(levelname)s> %(message)s',
        datefmt='%Y%m%d %H:%M:%S',
        filename=r'backtesting_%s.log' % datetime.now().strftime('%Y%m%d%H%M%S'),
        filemode='a')

    # -------------------------------------------------
    # 单策略的参数组全排列
    # setting = {'kkDev': [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    #            'trailingPrcnt_dev': [60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160],
    #            'kkLength': [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200],
    #            'long_kklength': [300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100,
    #                              1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800,
    #                              1900, 2000, 2100, 2200, 2300, 2400, 2500]}
    # parameter_groups_dict = setting_to_parameter_groups_dict(setting)
    # all_combination_strategy_ctabacktesting(parameter_groups_dict, strategy, 'rb0000')
    # --------------------------------------------------
    # --------------------------------------------------
    # 单策略的各个参数组
    # setting = [
    #     {'kkDev': 6,
    #      'trailingPrcnt_dev': 120,
    #      'kkLength': 50,
    #      'long_kklength': 500},
    #     {'kkDev': 8,
    #      'trailingPrcnt_dev': 120,
    #      'kkLength': 50,
    #      'long_kklength': 700}
    # ]
    setting = [{}]
    combination_strategy_ctabacktesting(setting, strategy, 'rb1710')
    # --------------------------------------------------
