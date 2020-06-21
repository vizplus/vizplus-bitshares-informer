import collections
import sys
from datetime import datetime, timedelta

from bitshares.amount import Amount
from bitshares.market import Market
from bitshares.price import Order

class Parser():
    def __init__(self, sett, **kwargs):
        """
        Инициализация класса, рынков и получение цены BTS

        :param set sett: настройки класса
            str quote - актив, стоимость которого считаем
            str base - актив, в котором считаем стоимость
            list additional_assets - дополнительные рынки для расчета, кроме BTS
            list usdt_assets - дополнительные рынки, стоимость которых равна 
                               стоимости актива base
            float base_depth - глубина расчета цены в стаканах в активе base
            float history_depth - глубина расчета цены совершенных сделок в 
                                  активе base
            int price_precision - количество знаков после запятой, для
                                  отображения цен
            int orderbook_limit - максимальное количество сделок из стакана
                                  получаемое от ноды
            int history_limit - максимальное количество сделок получаемое из
                                истории от ноды
            int history_period - максимальное количество дней, за которые
                                 берется история
            set viz_account - данные аккаунта для публикации в блокчейне VIZ
        """
        self.sett = sett
        self.quote_market = Market(self.sett['quote'] + ':BTS')
        self.base_market = Market('BTS:' + self.sett['base'])
        book = self.base_market.orderbook(limit=1)
        self.price = {}
        self.price['BTS'] = (book['asks'][0]['price'] + 
                             book['bids'][0]['price']) / 2
        self.bids = []
        self.asks = []

    def check_ask(self, base, core):
        """
        Функция для создания нового "виртуального" ордера в формате пары
        self.sett['quote'] / BTS
        Возвращает True в случае попадания этого ордера в выборку и False в
        противном случае

        :param bitshares.price.Order base: ордер на продажу из пары 
            self.sett['quote'] / BTS
        :param bitshares.price.Order core: ордер на продажу из пары 
            BTS / self.sett['base']

        Функция проверяет объемы в ордерах base и core и создает новый на основе
        меньшего из них
        """
        base_amount = base['base']['amount']
        core_amount = core['quote']['amount']
        if base_amount >= core_amount:
            new_base = base.copy()
            new_base['quote'] = Amount(
                core_amount / base['price'], 
                base['quote']['asset']
            )
            new_base['base'] = core['quote']
            order = Order(new_base['quote'], core['base'])
        else:
            new_core = core.copy()
            new_core['base'] = Amount(
                base_amount * core['price'], 
                core['base']['asset']
            )
            new_core['quote'] = base['base']
            order = Order(base['quote'], new_core['base'])
        return self.create_asks([order])

    def check_bid(self, base, core):
        """
        Функция для создания нового "виртуального" ордера в формате пары
        self.sett['quote'] / BTS
        Возвращает True в случае попадания этого ордера в выборку и False в 
        противном случае

        :param bitshares.price.Order base: ордер на покупку из пары 
            self.sett['quote'] / BTS
        :param bitshares.price.Order core: ордер на покупку из пары
            BTS / self.sett['base']

        Функция проверяет объемы в ордерах base и core и создает новый на основе
        меньшего из них
        """
        base_amount = base['base']['amount']
        core_amount = core['quote']['amount']
        if base_amount >= core_amount:
            new_base = base.copy()
            new_base['quote'] = Amount(
                core_amount / base['price'], 
                base['quote']['asset']
            )
            new_base['base'] = core['quote']
            order = Order(new_base['quote'], core['base'])
        else:
            new_core = core.copy()
            new_core['base'] = Amount(
                base_amount * core['price'], 
                core['base']['asset']
            )
            new_core['quote'] = base['base']
            order = Order(base['quote'], new_core['base'])
        return self.create_bids([order])

    def create_asks(self, asks):
        """
        Функция для формирования выборки ордеров на продажу.
        Возвращает True в случае попадания первого ордера в выборку и False в
        противном случае

        :param list(bitshares.price.Order) asks: список ордеров на продажу в
            формате пары self.sett['quote'] / BTS

        Функция сортирует ордера в порядке увеличения цены и отсекает все,
        которые не вписываются в параметр self.sett['base_depth']
        """
        tmp_asks = self.asks
        tmp_asks.extend(asks)
        tmp_asks.sort()
        self.asks = []
        asks_amount = 0
        result = False
        for ask in tmp_asks:
            self.asks.append(ask)
            if ask == asks[0]:
                result = True
            amount = ask['base']['amount'] * self.price['BTS']
            asks_amount += amount
            if asks_amount > self.sett['base_depth']:
                break
        return result

    def create_bids(self, bids):
        """
        Функция для формирования выборки ордеров на покупку.
        Возвращает True в случае попадания первого ордера в выборку и False в
        противном случае

        :param list(bitshares.price.Order) bids: список ордеров на покупку в
            формате пары self.sett['quote'] / BTS

        Функция сортирует ордера в порядке уменьшения цены и отсекает все,
        которые не вписываются в параметр self.sett['base_depth']
        """
        tmp_bids = self.bids
        tmp_bids.extend(bids)
        tmp_bids.sort(reverse=True)
        self.bids = []
        bids_amount = 0
        result = False
        for bid in tmp_bids:
            self.bids.append(bid)
            if bid == bids[0]:
                result = True
            amount = bid['base']['amount'] * self.price['BTS']
            bids_amount += amount
            if bids_amount > self.sett['base_depth']:
                break
        return result

    def get_additional_orderbook(self):
        """
        Функция для проверки ордеров в стаканах пар указанные в параметре
        self.sett['additional_assets']

        Функция получает из сети BitShares данные из всех стаканов указанных в
        параметре self.sett['additional_assets'] и формирует выборку на основе
        этих данных. Результаты ее работы сохраняются в переменных класса
        self.bids и self.asks
        """
        for asset in self.sett['additional_assets']:
            market_base = Market(self.sett['quote'] + ':' + asset)
            market_core = Market(asset + ':BTS')
            book_base = market_base.orderbook(
                limit=self.sett['orderbook_limit']
            )
            book_core = market_core.orderbook(
                limit=self.sett['orderbook_limit']
            )
            for bid_base in book_base['bids']:
                check = False
                base_amount = bid_base['base']['amount']
                bid_core = book_core['bids'][0]
                while base_amount > 0:
                    core_amount = bid_core['quote']['amount']
                    check = self.check_bid(bid_base, bid_core)
                    if base_amount >= core_amount:
                        bid_base['quote'] -= Amount(
                            core_amount / bid_base['price'], 
                            bid_base['quote']['asset']
                        )
                        bid_base['base'] -= bid_core['quote']
                        book_core['bids'].pop(0)
                        bid_core = book_core['bids'][0]
                    else:
                        bid_core['base'] -= Amount(
                            base_amount * bid_core['price'], 
                            bid_core['base']['asset']
                        )
                        bid_core['quote'] -= bid_base['base']
                        break
                    if not check:
                        base_amount = 0
                    else:
                        base_amount = bid_base['base']['amount']
                if not check:
                    break
            for ask_base in book_base['asks']:
                check = False
                base_amount = ask_base['base']['amount']
                ask_core = book_core['asks'][0]
                while base_amount > 0:
                    core_amount = ask_core['quote']['amount']
                    check = self.check_ask(ask_base, ask_core)
                    if base_amount >= core_amount:
                        ask_base['quote'] -= Amount(
                            core_amount / ask_base['price'], 
                            ask_base['quote']['asset']
                        )
                        ask_base['base'] -= ask_core['quote']
                        book_core['asks'].pop(0)
                        ask_core = book_core['asks'][0]
                    else:
                        ask_core['base'] -= Amount(
                            base_amount * ask_core['price'], 
                            ask_core['base']['asset']
                        )
                        ask_core['quote'] -= ask_base['base']
                        break
                    if not check:
                        base_amount = 0
                    else:
                        base_amount = ask_base['base']['amount']
                if not check:
                    break

    def get_history_depth(self):
        """
        Функция для рассчета средней цены совершенных сделок

        Функция собирает все данные из истории, сортирует их по дате, приводит
        цены к self.sett['base'] и отсекает все сделки выходящие за пределы
        self.sett['history_depth']. Результаты сохраняет в переменных класса
        self.history_amount и self.average_history_price
        """
        history = []
        sum = 0
        start_time = datetime.now() - timedelta(
            days=self.sett['history_period']
        )
        for trade in self.quote_market.trades(
            limit=self.sett['history_limit'], 
            start=start_time
        ):
            amount = trade['base']['amount'] * self.price['BTS']
            history.append(trade)
            sum += amount
            if sum > self.sett['history_depth']:
                break
        history.sort(key=self.sortByTime, reverse=True)
        assets = self.sett['additional_assets'].copy()
        assets.extend(self.sett['usdt_assets'])
        for asset in assets:
            market = Market(asset + ':BTS')
            book = market.orderbook(limit=1)
            self.price[asset] = (book['asks'][0]['price'] + 
                                 book['bids'][0]['price']) / 2*self.price['BTS']
            market = Market(self.sett['quote'] + ':' + asset)
            for trade in market.trades(
                limit=self.sett['history_limit'], 
                start=start_time
            ):
                history.append(trade)
                history.sort(key=self.sortByTime, reverse=True)
                amount = trade['base']['amount'] * self.price[asset]
                sum += amount
                break_bool = False
                while sum >= self.sett['history_depth']:
                    last = history.pop()
                    last_amount = (last['base']['amount'] * 
                                   self.price[last['base']['symbol']])
                    if last_amount > sum - self.sett['history_depth']:
                        history.append(last)
                        break
                    else:
                        sum -= last_amount
                    if collections.Counter(last) == collections.Counter(trade):
                        break_bool = True
                        break
                if break_bool:
                    break
        sum = sum_quote = 0
        for h in history:
            sum += h['base']['amount'] * self.price[h['base']['symbol']]
            sum_quote += h['quote']['amount']
        if sum > self.sett['history_depth']:
            last = history.pop()
            ratio = sum / self.sett['history_depth']
            sum_quote = last['quote']['amount'] / ratio
            sum = self.sett['history_depth']
        self.history_amount = sum_quote
        self.average_history_price = sum / sum_quote

    def get_market_depth(self):
        """
        Основная функция для расчета средней цены ордеров в стакане

        Функция поочередно вызывает дочерние функции self.get_orderbook(),
        self.get_additional_orderbook(), self.get_usdt_orderbook() для сбора
        ордеров из всех пар. А затем расчитывает среднюю цену и сохраняет данные
        в переменных класса self.average_bid_price и self.average_ask_price
        """
        self.get_orderbook()
        self.get_additional_orderbook()
        self.get_usdt_orderbook()
        quote = base = sum = 0
        for bid in self.bids:
            amount = bid['base']['amount'] * self.price['BTS']
            if sum + amount <= self.sett['base_depth']:
                quote += bid['quote']['amount']
                base += bid['base']['amount']
                sum += amount
            else:
                diff = self.sett['base_depth'] - sum
                ratio = diff / amount
                quote += bid['quote']['amount'] * ratio
                base += bid['base']['amount'] * ratio
                sum += diff
        self.average_bid_price = base / quote * self.price['BTS']
        quote = base = sum = 0
        for ask in self.asks:
            amount = ask['base']['amount'] * self.price['BTS']
            if sum + amount <= self.sett['base_depth']:
                quote += ask['quote']['amount']
                base += ask['base']['amount']
                sum += amount
            else:
                diff = self.sett['base_depth'] - sum
                ratio = diff / amount
                quote += ask['quote']['amount'] * ratio
                base += ask['base']['amount'] * ratio
                sum += diff
        self.average_ask_price = base / quote * self.price['BTS']

    def get_orderbook(self):
        """
        Функция получает ордера из пары self.sett['quote'] / BTS
        """
        orderbook = self.quote_market.orderbook(
            limit=self.sett['orderbook_limit']
        )
        self.create_bids(orderbook['bids'])
        self.create_asks(orderbook['asks'])

    def get_usdt_orderbook(self):
        """
        Функция для проверки ордеров в стаканах пар указанные в параметре
        self.sett['usdt_assets']

        Функция получает из сети BitShares данные из всех стаканов указанных в
        параметре self.sett['usdt_assets'] и формирует выборку на основе этих
        данных. Результаты ее работы сохраняются в переменных класса self.bids и
        self.asks
        """
        for asset in self.sett['usdt_assets']:
            market = Market(self.sett['quote'] + ':' + asset)
            book = market.orderbook(
                limit=self.sett['orderbook_limit']
            )
            for bid in book['bids']:
                amount = bid['base']['amount']
                bid = Order(
                    bid['quote'], 
                    Amount(amount / self.price['BTS'], 'BTS')
                )
                if not self.create_bids([bid]):
                    break
            for ask in book['asks']:
                amount = ask['base']['amount']
                ask = Order(
                    ask['quote'], 
                    Amount(amount / self.price['BTS'], 'BTS')
                )
                if not self.create_asks([ask]):
                    break

    def sortByTime(self, input):
        """
        Вспомогательная функция для сортировки
        """
        return input['time']
