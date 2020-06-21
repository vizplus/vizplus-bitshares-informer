import decimal
from datetime import datetime

from bitshares import BitShares
from bitshares.instance import set_shared_bitshares_instance

# класс с расчетом цен на бирже BitShares
from btsParser.Parser import Parser
# класс для работы с VIZ (от Протея)
from tvizbase.api import Api

decimal.getcontext().rounding = 'ROUND_HALF_UP'
# подключение к ноде node в сети Bitshares
BTS = BitShares(
    node='wss://citadel.li/node'
)
set_shared_bitshares_instance(BTS)
# подключение к сети VIZ
viz = Api()
# Основные настройки скрипта
# quote - актив, стоимость которого считаем
# base - актив, в котором считаем стоимость
# additional_assets - дополнительные рынки для расчета, кроме BTS
# usdt_assets - дополнительные рынки, стоимость которых равна стоимости
#   актива base
# base_depth - глубина расчета цены в стаканах в активе base
# history_depth - глубина расчета цены совершенных сделок в активе base
# price_precision - количество знаков после запятой, для отображения цен
# orderbook_limit - максимальное количество сделок из стакана получаемое от ноды
# history_limit - максимальное количество сделок получаемое из истории от ноды
# history_period - максимальное количество дней, за которые берется история
# viz_account - данные аккаунта для публикации в блокчейне VIZ
settings = {
    'quote': 'XCHNG.VIZ',
    'base': 'GDEX.USDT',
    'additional_assets': ['RUDEX.GOLOS', 'RUBLE'],
    'usdt_assets': ['RUDEX.USDT'],
    'base_depth': 100,
    'history_depth': 100,
    'price_precision': 5,
    'orderbook_limit': 50,
    'history_limit': 100,
    'history_period': 30,
    'viz_account': {
        'login': '...', 
        'key': '5...'
    }
}
# инициализация класса
parser = Parser(settings)
# получение данных о глубине стаканов
parser.get_market_depth()
# получение данных об истории сделок
parser.get_history_depth()
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
            'average_history_price': str(decimal.Decimal(
                parser.average_history_price
            ).quantize(decimal.Decimal('1.' + '0'*settings['price_precision']))), 
            'quote': parser.sett['quote'],
            'base': parser.sett['base'],
            'additional_assets': parser.sett['additional_assets'],
            'usdt_assets': parser.sett['usdt_assets'],
            'base_depth': parser.sett['base_depth'],
            'history_depth': parser.sett['history_depth']
        }
    ], 
    settings['viz_account']['login'], 
    settings['viz_account']['key']
)
