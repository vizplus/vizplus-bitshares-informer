# vizplus-bitshares-info

## Required libraries

### Install with pip3:

    $ sudo apt-get install libffi-dev libssl-dev python-dev python3-dev python3-pip
    $ pip3 install bitshares
    $ pip3 install --upgrade requests

### Значения параметров в settings

 "quote": основной токен, чей курс считаем
 "base": валюта, в которой считаем курс
 "additional_assets": пары, которые учитываем при подсчёте курса 
 "usdt_assets": пары, которые не надо пересчитывать через курс bts, их берём как есть
 "base_depth": глубина стакана, для которой считаем курс, выражается в base (для нас - доллары)
 "history_depth": не используется сейчас
 "price_precision": точность подсчёта курса, количество знаков после запятой
 "orderbook_limit": максимальное учитываемое количество ордеров для каждой пары 
 "history_limit": не используется сейчас
 "history_period": не используется сейчас
 "viz_account": данные аккаунта VIZ, в котором публикуется курс
