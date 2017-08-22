# encoding: UTF-8

import copy
import shelve
from collections import OrderedDict
from datetime import datetime

import xml.etree.ElementTree as ElementTree

from eventEngine import *
from vtGateway import *

from ctpGateway.ctpGateway import CtpGateway
from ctaStrategy.ctaEngine import CtaEngine

from mysql_operation import *


########################################################################
class MainEngine(object):
    """主引擎"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        # 记录今日日期
        self.todayDate = datetime.now().strftime('%Y%m%d')
        self.ctp_get_all_contract = False

        # 创建事件引擎
        self.eventEngine = EventEngine2()
        self.eventEngine.start()

        # 创建数据引擎
        self.dataEngine = DataEngine(self.eventEngine)

        # mysql本地数据库相关
        self.cnx = None  # mysql对象

        # 调用一个个初始化函数
        self.initGateway()

        # 扩展模块
        self.ctaEngine = CtaEngine(self, self.eventEngine)

    # ----------------------------------------------------------------------
    def initGateway(self):
        """初始化接口对象"""
        # 用来保存接口对象的字典
        self.gateway = CtpGateway(self.eventEngine)
        self.gateway.setQryEnabled(True)

    # ----------------------------------------------------------------------
    def connect(self):
        """连接ctp名称的接口"""
        self.gateway.connect()
        self.ctp_get_all_contract = self.gateway.tdApi.ctp_get_all_contract_info

    # ----------------------------------------------------------------------
    def subscribe(self, subscribeReq):
        """订阅ctp接口的行情"""
        self.gateway.subscribe(subscribeReq)

    # ----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """对ctp接口发单"""
        return self.gateway.sendOrder(orderReq)

    # ----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """对ctp接口撤单"""
        self.gateway.cancelOrder(cancelOrderReq)

    # ----------------------------------------------------------------------
    def qryAccount(self):
        """查询ctp接口的账户"""
        self.gateway.qryAccount()

    # ----------------------------------------------------------------------
    def qryPosition(self):
        """查询ctp接口的持仓"""
        self.gateway.qryPosition()

    # ----------------------------------------------------------------------
    def exit(self):
        """退出程序前调用，保证正常退出"""
        # 安全关闭所有接口
        self.gateway.close()

        # 停止事件引擎
        self.eventEngine.stop()

    # ----------------------------------------------------------------------
    def writeLog(self, content):
        """快速发出日志事件"""
        log = VtLogData()
        log.logContent = content
        event = Event(type_=EVENT_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)

    # ----------------------------------------------------------------------
    @staticmethod
    def update_strategy_config(strategy_config_file, d):
        tree = ElementTree.parse(strategy_config_file)
        if ((d['offset'] == '开仓') and (d['direction'] == '多')) or (('平' in d['offset']) and (d['direction'] == '空')):
            direction = "long"
            pos = d['long_pos']
        elif ((d['offset'] == '开仓') and (d['direction'] == '空')) or (('平' in d['offset']) and (d['direction'] == '多')):
            direction = "short"
            pos = d['short_pos']
        else:
            print("can't update strategy position")
            print(d)
            return
        positions = tree.findall('position/{dir}'.format(dir=direction))
        for position in positions:
            for s in position:
                if s.get('instrument') == d['symbol']:
                    for h in position:
                        if h.get('quantity'):
                            h.set('quantity', str(pos))
                        if h.get('datetime'):
                            h.set('datetime', d['tradeTime'])
        tree.write(strategy_config_file, encoding="UTF-8", xml_declaration=True)

    # ----------------------------------------------------------------------
    @staticmethod
    def parse_strategy_config(strategy_config_file):
        strategy_positions = dict()
        tree = ElementTree.parse(strategy_config_file)
        root = tree.getroot()
        # 得到symbol tree内的所有信息
        strategy_name = ''
        for level1 in root:
            if level1.tag == "name":
                strategy_name = level1.text
            if level1.tag == "position":
                for position in level1:
                    if position.tag == "long":
                        for long in position:
                            strategy_position = dict()
                            strategy_position['name'] = strategy_name
                            strategy_position['contract'] = str(long.get("instrument"))
                            strategy_position['quantity'] = int(1) * int(long.get("quantity"))
                            strategy_position['datetime'] = datetime.strptime(str(long.get("datetime")),
                                                                              "%Y-%m-%d %H:%M:%S")
                            strategy_positions['long'] = strategy_position
                    elif position.tag == "short":
                        for short in position:
                            strategy_position = dict()
                            strategy_position['name'] = strategy_name
                            strategy_position['contract'] = str(short.get("instrument"))
                            strategy_position['quantity'] = int(-1) * int(short.get("quantity"))
                            strategy_position['datetime'] = datetime.strptime(str(short.get("datetime")),
                                                                              "%Y-%m-%d %H:%M:%S")
                            strategy_positions['short'] = strategy_position
        return strategy_positions

    # ----------------------------------------------------------------------
    def getContract(self, vtSymbol):
        """查询合约"""
        return self.dataEngine.getContract(vtSymbol)

    # ----------------------------------------------------------------------
    def getAllContracts(self):
        """查询所有合约（返回列表）"""
        return self.dataEngine.getAllContracts()

    # ----------------------------------------------------------------------
    def getOrder(self, vtOrderID):
        """查询委托"""
        return self.dataEngine.getOrder(vtOrderID)

    # ----------------------------------------------------------------------
    def getAllWorkingOrders(self):
        """查询所有的活跃的委托（返回列表）"""
        return self.dataEngine.getAllWorkingOrders()

    # ----------------------------------------------------------------------
    def __del__(self):
        if self.cnx:
            self.cnx.close()


########################################################################
class DataEngine(object):
    """数据引擎"""
    contractFileName = 'ContractData.vt'

    # ----------------------------------------------------------------------
    def __init__(self, eventEngine):
        """Constructor"""
        self.eventEngine = eventEngine

        # 保存合约详细信息的字典
        self.contractDict = {}

        # 保存委托数据的字典
        self.orderDict = {}

        # 保存活动委托数据的字典（即可撤销）
        self.workingOrderDict = {}

        # 注册事件监听
        self.registerEvent()

    # ----------------------------------------------------------------------
    def updateContract(self, event):
        """更新合约数据"""
        contract = event.dict_['data']
        self.contractDict[contract.vtSymbol] = contract
        self.contractDict[contract.symbol] = contract  # 使用常规代码（不包括交易所）可能导致重复

    # ----------------------------------------------------------------------
    def getContract(self, vtSymbol):
        """查询合约对象"""
        try:
            return self.contractDict[vtSymbol]
        except KeyError:
            return None

    # ----------------------------------------------------------------------
    def getAllContracts(self):
        """查询所有合约对象（返回列表）"""
        return list(self.contractDict.values())

    # ----------------------------------------------------------------------
    def updateOrder(self, event):
        """更新委托数据"""
        order = event.dict_['data']
        self.orderDict[order.vtOrderID] = order

        # 如果订单的状态是全部成交或者撤销，则需要从workingOrderDict中移除
        if order.status == STATUS_ALLTRADED or order.status == STATUS_CANCELLED:
            if order.vtOrderID in self.workingOrderDict:
                del self.workingOrderDict[order.vtOrderID]
        # 否则则更新字典中的数据
        else:
            self.workingOrderDict[order.vtOrderID] = order

    # ----------------------------------------------------------------------
    def getOrder(self, vtOrderID):
        """查询委托"""
        try:
            return self.orderDict[vtOrderID]
        except KeyError:
            return None

    # ----------------------------------------------------------------------
    def getAllWorkingOrders(self):
        """查询所有活动委托（返回列表）"""
        return list(self.workingOrderDict.values())

    # ----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_CONTRACT, self.updateContract)
        self.eventEngine.register(EVENT_ORDER, self.updateOrder)
