# encoding: UTF-8

"""
本模块中主要包含：
1. 从通联数据下载历史行情的引擎
2. 用来把MultiCharts导出的历史数据载入到MongoDB中用的函数
3. 增加从通达信导出的历史数据载入到MongoDB中的函数
"""

import os
import sys

file_path = os.path.abspath(__file__)
folder_path = os.path.dirname(file_path)
root_path = os.path.dirname(folder_path)
history_data_path = os.path.join(root_path, "history_data")
ctaStrategy_path = os.path.join(root_path, "ctaStrategy")
sys.path.append(ctaStrategy_path)

import csv
import datetime as dt
from ctaBase import *


# ----------------------------------------------------------------------
def loadMcCsv(fileName, symbol):
    """将Multicharts导出的csv格式的历史数据插入到Mongo数据库中"""
    history_data_file = os.path.join(history_data_path, fileName + ".csv")
    symbol_data = os.path.join(history_data_path, symbol + ".csv")
    print(history_data_file)
    # 读取数据和插入到数据库
    reader = csv.DictReader(open(history_data_file, 'r'))
    data = []
    for d in reader:
        bar = CtaBarData()
        bar.vtSymbol = str(d['instrument'])
        bar.symbol = bar.vtSymbol
        bar.open = float(d['open'])
        bar.high = float(d['high'])
        bar.low = float(d['low'])
        bar.close = float(d['close'])
        datetime = str((int(d['date']) * 1000000 + int(d['time'])))
        bar.datetime = str(dt.datetime.strptime(datetime, '%Y%m%d%H%M%S'))
        bar.volume = d['volume']
        bar.openInterest = d['open_int']
        data.append(bar.__dict__)
        print(bar.datetime)

    with open(symbol_data, 'w') as fid:
        csv.unix_dialect.quoting = 0
        writer = csv.DictWriter(fid, ['vtSymbol', 'symbol', 'exchange','datetime',  'date', 'time', 'open', 'high', 'low', 'close', 'volume', 'openInterest'], dialect=csv.unix_dialect)
        writer.writeheader()
        writer.writerows(data)


if __name__ == '__main__':
    loadMcCsv('au1712_1min_kbar', 'au1712')
    loadMcCsv('rb1710_1min_kbar', 'rb1710')
    loadMcCsv('rb1801_1min_kbar', 'rb1801')
