# encoding: UTF-8

# 默认空值
EMPTY_STRING = ''
EMPTY_UNICODE = u''
EMPTY_INT = 0
EMPTY_FLOAT = 0.0

# 方向常量
DIRECTION_NONE = u'无方向'
DIRECTION_LONG = u'多'
DIRECTION_SHORT = u'空'
DIRECTION_UNKNOWN = u'未知'
DIRECTION_NET = u'净'
DIRECTION_SELL = u'卖出'  # IB接口

# 开平常量
OFFSET_NONE = u'无开平'
OFFSET_OPEN = u'开仓'
OFFSET_CLOSE = u'平仓'
OFFSET_CLOSETODAY = u'平今'
OFFSET_CLOSEYESTERDAY = u'平昨'
OFFSET_UNKNOWN = u'未知'

# 状态常量
STATUS_NOTTRADED = u'未成交'
STATUS_PARTTRADED = u'部分成交'
STATUS_ALLTRADED = u'全部成交'
STATUS_CANCELLED = u'已撤销'
STATUS_UNKNOWN = u'未知'

# 合约类型常量
PRODUCT_EQUITY = u'股票'
PRODUCT_FUTURES = u'期货'
PRODUCT_OPTION = u'期权'
PRODUCT_INDEX = u'指数'
PRODUCT_COMBINATION = u'组合'
PRODUCT_FOREX = u'外汇'
PRODUCT_UNKNOWN = u'未知'
PRODUCT_SPOT = u'现货'
PRODUCT_DEFER = u'延期'
PRODUCT_NONE = ''

# 价格类型常量
PRICETYPE_LIMITPRICE = u'限价'
PRICETYPE_MARKETPRICE = u'市价'
PRICETYPE_FAK = u'FAK'
PRICETYPE_FOK = u'FOK'

# 期权类型
OPTION_CALL = u'看涨期权'
OPTION_PUT = u'看跌期权'

# 交易所类型
EXCHANGE_SSE = 'SSE'  # 上交所
EXCHANGE_SZSE = 'SZSE'  # 深交所
EXCHANGE_CFFEX = 'CFFEX'  # 中金所
EXCHANGE_SHFE = 'SHFE'  # 上期所
EXCHANGE_CZCE = 'CZCE'  # 郑商所
EXCHANGE_DCE = 'DCE'  # 大商所
EXCHANGE_SGE = 'SGE'  # 上金所
EXCHANGE_INE = 'INE'  # 上海国际能源交易中心
EXCHANGE_UNKNOWN = 'UNKNOWN'  # 未知交易所
EXCHANGE_NONE = ''  # 空交易所
EXCHANGE_HKEX = 'HKEX'  # 港交所
EXCHANGE_HKFE = 'HKFE'  # 香港期货交易所

EXCHANGE_SMART = 'SMART'  # IB智能路由（股票、期权）
EXCHANGE_NYMEX = 'NYMEX'  # IB 期货
EXCHANGE_GLOBEX = 'GLOBEX'  # CME电子交易平台
EXCHANGE_IDEALPRO = 'IDEALPRO'  # IB外汇ECN

EXCHANGE_CME = 'CME'  # CME交易所
EXCHANGE_ICE = 'ICE'  # ICE交易所

EXCHANGE_OANDA = 'OANDA'  # OANDA外汇做市商
EXCHANGE_OKCOIN = 'OKCOIN'  # OKCOIN比特币交易所
EXCHANGE_HUOBI = 'HUOBI'  # 火币比特币交易所
EXCHANGE_LHANG = 'LHANG'  # 链行比特币交易所

# 货币类型
CURRENCY_USD = 'USD'  # 美元
CURRENCY_CNY = 'CNY'  # 人民币
CURRENCY_HKD = 'HKD'  # 港币
CURRENCY_UNKNOWN = 'UNKNOWN'  # 未知货币
CURRENCY_NONE = ''  # 空货币

# 数据库
LOG_DB_NAME = 'ctp_log'

# 接口类型
GATEWAYTYPE_EQUITY = 'equity'  # 股票、ETF、债券
GATEWAYTYPE_FUTURES = 'futures'  # 期货、期权、贵金属
GATEWAYTYPE_INTERNATIONAL = 'international'  # 外盘
GATEWAYTYPE_BTC = 'btc'  # 比特币
GATEWAYTYPE_DATA = 'data'  # 数据（非交易）

# 系统相关
EVENT_TIMER = 'eTimer'  # 计时器事件，每隔1秒发送一次
EVENT_LOG = 'eLog'  # 日志事件，全局通用

# Gateway相关
EVENT_TICK = 'eTick.'  # TICK行情事件，可后接具体的vtSymbol
EVENT_TRADE = 'eTrade.'  # 成交回报事件
EVENT_ORDER = 'eOrder.'  # 报单回报事件
EVENT_POSITION = 'ePosition.'  # 持仓回报事件
EVENT_ACCOUNT = 'eAccount.'  # 账户回报事件
EVENT_CONTRACT = 'eContract.'  # 合约基础信息回报事件
EVENT_ERROR = 'eError.'  # 错误回报事件

# CTA模块相关
EVENT_CTA_LOG = 'eCtaLog'  # CTA相关的日志事件
EVENT_CTA_STRATEGY = 'eCtaStrategy.'  # CTA策略状态变化事件

# 行情记录模块相关
EVENT_DATARECORDER_LOG = 'eDataRecorderLog'  # 行情记录日志更新事件

SAVE_DATA = u'保存数据'

CONTRACT_SYMBOL = u'合约代码'
CONTRACT_NAME = u'名称'
LAST_PRICE = u'最新价'
PRE_CLOSE_PRICE = u'昨收盘'
VOLUME = u'成交量'
OPEN_INTEREST = u'持仓量'
OPEN_PRICE = u'开盘价'
HIGH_PRICE = u'最高价'
LOW_PRICE = u'最低价'
TIME = u'时间'
GATEWAY = u'接口'
CONTENT = u'内容'

ERROR_CODE = u'错误代码'
ERROR_MESSAGE = u'错误信息'

TRADE_ID = u'成交编号'
ORDER_ID = u'委托编号'
DIRECTION = u'方向'
OFFSET = u'开平'
PRICE = u'价格'
TRADE_TIME = u'成交时间'
USE_MARGIN = u'占用保证金'


ORDER_VOLUME = u'委托数量'
TRADED_VOLUME = u'成交数量'
ORDER_STATUS = u'委托状态'
ORDER_TIME = u'委托时间'
CANCEL_TIME = u'撤销时间'
FRONT_ID = u'前置编号'
SESSION_ID = u'会话编号'
POSITION = u'持仓量'
YD_POSITION = u'昨持仓'
FROZEN = u'冻结量'
POSITION_PROFIT = u'持仓盈亏'

ACCOUNT_ID = u'账户'
PRE_BALANCE = u'昨日结算净值'
BALANCE = u'动态净值'
AVAILABLE = u'可用资金'
COMMISSION = u'手续费'
MARGIN = u'占用保证金'
CLOSE_PROFIT = u'平仓盈亏'

TRADING = u'交易'
PRICE_TYPE = u'价格类型'
EXCHANGE = u'交易所'
CURRENCY = u'货币'
PRODUCT_CLASS = u'产品类型'
LAST = u'最新'
SEND_ORDER = u'发单'
CANCEL_ALL = u'全撤'
VT_SYMBOL = u'vt系统代码'
CONTRACT_SIZE = u'合约大小'
PRICE_TICK = u'最小价格变动'
STRIKE_PRICE = u'行权价'
UNDERLYING_SYMBOL = u'标的代码'
OPTION_TYPE = u'期权类型'

REFRESH = u'刷新'
SEARCH = u'查询'
CONTRACT_SEARCH = u'合约查询'

BID_1 = u'买一'
BID_2 = u'买二'
BID_3 = u'买三'
BID_4 = u'买四'
BID_5 = u'买五'
ASK_1 = u'卖一'
ASK_2 = u'卖二'
ASK_3 = u'卖三'
ASK_4 = u'卖四'
ASK_5 = u'卖五'

BID_PRICE_1 = u'买一价'
BID_PRICE_2 = u'买二价'
BID_PRICE_3 = u'买三价'
BID_PRICE_4 = u'买四价'
BID_PRICE_5 = u'买五价'
ASK_PRICE_1 = u'卖一价'
ASK_PRICE_2 = u'卖二价'
ASK_PRICE_3 = u'卖三价'
ASK_PRICE_4 = u'卖四价'
ASK_PRICE_5 = u'卖五价'

BID_VOLUME_1 = u'买一量'
BID_VOLUME_2 = u'买二量'
BID_VOLUME_3 = u'买三量'
BID_VOLUME_4 = u'买四量'
BID_VOLUME_5 = u'买五量'
ASK_VOLUME_1 = u'卖一量'
ASK_VOLUME_2 = u'卖二量'
ASK_VOLUME_3 = u'卖三量'
ASK_VOLUME_4 = u'卖四量'
ASK_VOLUME_5 = u'卖五量'

MARKET_DATA = u'行情'
LOG = u'日志'
ERROR = u'错误'
TRADE = u'成交'
ORDER = u'委托'
POSITION = u'持仓'
ACCOUNT = u'账户'

SYSTEM = u'系统'
CONNECT_DATABASE = u'连接数据库'
EXIT = u'退出'
APPLICATION = u'功能'
DATA_RECORDER = u'行情记录'
RISK_MANAGER = u'风控管理'

STRATEGY = u'策略'
CTA_STRATEGY = u'CTA策略'

HELP = u'帮助'
RESTORE = u'还原'
ABOUT = u'关于'
TEST = u'测试'
CONNECT = u'连接'

CPU_MEMORY_INFO = u'CPU使用率：{cpu}%   内存使用率：{memory}%'
CONFIRM_EXIT = u'确认退出？'

RISK_MANAGER = u'风控管理'

RISK_MANAGER_STOP = u'风控模块未启动'
RISK_MANAGER_RUNNING = u'风控模块运行中'
CLEAR_ORDER_FLOW_COUNT = u'清空流控计数'
CLEAR_TOTAL_FILL_COUNT = u'清空总成交计数'
SAVE_SETTING = u'保存设置'

WORKING_STATUS = u'工作状态'
ORDER_FLOW_LIMIT = u'流控上限'
ORDER_FLOW_CLEAR = u'流控清空（秒）'
ORDER_SIZE_LIMIT = u'单笔委托上限'
TOTAL_TRADE_LIMIT = u'总成交上限'
WORKING_ORDER_LIMIT = u'活动订单上限'
CONTRACT_CANCEL_LIMIT = u'单合约撤单上限'

DATA_RECORDER = u'行情记录'

TICK_RECORD = u'Tick记录'
BAR_RECORD = u'Bar记录'
TICK_RECORD = u'Tick记录'

CONTRACT_SYMBOL = u'合约代码'
GATEWAY = u'接口'

DOMINANT_CONTRACT = u'主力合约'
DOMINANT_SYMBOL = u'主力代码'

TICK_LOGGING_MESSAGE = u'记录Tick数据{symbol}，时间:{time}, last:{last}, bid:{bid}, ask:{ask}'
BAR_LOGGING_MESSAGE = u'记录分钟线数据{symbol}，时间:{time}, O:{open}, H:{high}, L:{low}, C:{close}'

INIT = u'初始化'
START = u'启动'
STOP = u'停止'

# 策略部分
CTA_ENGINE_STARTED = u'CTA引擎启动成功'

CTA_STRATEGY = u'CTA策略'
LOAD_STRATEGY = u'加载策略'
INIT_ALL = u'全部初始化'
START_ALL = u'全部启动'
STOP_ALL = u'全部停止'
SAVE_POSITION_DATA = u'保存持仓'

STRATEGY_LOADED = u'策略加载成功'

# 数据库名称
LONG_POSITION_DB_NAME = 'ctp_long_position'
SHORT_POSITION_DB_NAME = 'ctp_short_position'
TICK_DB_NAME = 'ctp_tick'
MINUTE_DB_NAME = 'ctp_1min'
