# vizplus-bitshares-info

## Required libraries

### Installing:

    $ git clone https://github.com/vizplus/vizplus-bitshares-info
    $ cd vizplus-bitshares-info
    $ sudo apt-get install libffi-dev libssl-dev python-dev python3-dev python3-pip python3-venv
    $ pip3 install --upgrade requests
    $ python3 -m venv venv
    $ . venv/bin/activate
    $ pip3 install bitshares
    $ deactivate
    
### Using:

    $ mv settings.json.example settings.json
    
Edit file settings.json and run script:

    $ venv/bin/python ./bot.py

### Значения параметров в settings

 "bitshares_node": адрес ноды BitShares
 
 "quote": основной токен, чей курс считаем
 
 "base": токен, в котором считаем курс. Если есть выбор (например, USDT от разных шлюзов), то лучше брать токен с наиболее реалистичным курсом и минимальным спредом к bts 
 
 "additional_assets": пары, которые учитываем при подсчёте курса 
 
 "usdt_assets": пары, которые не надо пересчитывать через курс bts, их берём как есть
 
 "base_depth": глубина стакана, для которой считаем курс, выражается в base (для нас - доллары)
 
 "history_depth": не используется сейчас
 
 "price_precision": точность подсчёта курса, количество знаков после запятой
 
 "orderbook_limit": максимальное учитываемое количество ордеров для каждой пары 
 
 "history_limit": не используется сейчас
 
 "history_period": не используется сейчас
 
 "viz_account": данные аккаунта VIZ, в котором публикуется курс
