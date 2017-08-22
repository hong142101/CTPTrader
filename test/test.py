from datetime import datetime
import xml.etree.ElementTree as ElementTree

strategy_config_file = r"E:\HX_python\CTPTrader_test\ctaStrategy\strategy\kkstrategy_rb_1.stg"

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
print(strategy_positions)
