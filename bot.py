import decimal
import json
import os
from datetime import datetime

from bitshares import BitShares
from bitshares.instance import set_shared_bitshares_instance

# класс с расчетом цен на бирже BitShares
from btsParser.Parser import Parser
# класс для работы с VIZ (от Протея)
from tvizbase.api import Api

with open(os.path.dirname(__file__) + '/settings.json', 'r') as sett_file:
    settings = json.load(sett_file)
decimal.getcontext().rounding = 'ROUND_HALF_UP'
# подключение к ноде node в сети Bitshares
BTS = BitShares(
    node=settings['bitshares_node']
)
set_shared_bitshares_instance(BTS)
# подключение к сети VIZ
viz = Api()
# инициализация класса
parser = Parser(settings)
# получение данных о глубине стаканов
parser.get_market_depth()
# получение данных об истории сделок
#parser.get_history_depth()
# публикация данных в блокчейне VIZ
viz.custom(
    'vizplus_bitshares_info', # ID custom'а 
    [
        'vizplus_bitshares_info', # название типа данных, может отличаться от ID
        {
            'datetime': str(datetime.now()),
            'average_bid_price': str(decimal.Decimal(
                parser.average_bid_price
            ).quantize(decimal.Decimal('1.' + '0'*settings['price_precision']))),
            'average_ask_price': str(decimal.Decimal(
                parser.average_ask_price
            ).quantize(decimal.Decimal('1.' + '0'*settings['price_precision']))),
            #'average_history_price': str(decimal.Decimal(
            #    parser.average_history_price
            #).quantize(decimal.Decimal('1.' + '0'*settings['price_precision']))), 
            'quote': parser.sett['quote'],
            'base': parser.sett['base'],
            'additional_assets': parser.sett['additional_assets'],
            'usdt_assets': parser.sett['usdt_assets'],
            'base_depth': parser.sett['base_depth'],
            #'history_depth': parser.sett['history_depth']
        }
    ], 
    settings['viz_account']['login'], 
    settings['viz_account']['key']
)
