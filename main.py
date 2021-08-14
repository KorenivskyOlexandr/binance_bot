import decimal
import json
import time

from binance.client import Client
from binance.exceptions import BinanceAPIException

from constant import binance_api_key, binance_api_secret_key
from decimal import Decimal
from binance_bot import send_notification_message

client = Client(binance_api_key, binance_api_secret_key)

SYMBOL_NAME = "ADAUSDT"
STABLE_NAME = "USDT"


class BarInfo():
    def __init__(self, symbol, currency_info):
        self.symbol = symbol
        self.open_time = currency_info[0]
        self.open_price = Decimal(currency_info[1])
        self.high_price = Decimal(currency_info[2])
        self.low_price = Decimal(currency_info[3])
        self.close_price = Decimal(currency_info[4])
        self.volume_crypto = Decimal(currency_info[5])
        self.close_time = currency_info[6]
        self.volume_fiat = Decimal(currency_info[7])

    def __str__(self):
        return f"{self.symbol}, open price = {self.open_price}, close price =  {self.close_price}, volume {self.volume_fiat}"


def create_named_data(symbol: str, bar_info: list) -> BarInfo:
    return BarInfo(symbol, bar_info[:8])


def get_average_value_of_volume(symbol: str) -> Decimal:
    ticker = client.get_ticker(symbol=symbol)
    volume = ticker.get("quoteVolume")
    return Decimal(volume) / Decimal(24)


def data_comparison(first_bar: BarInfo, second_bar: BarInfo) -> bool:
    if second_bar.close_price < Decimal('500'):
        if first_bar.volume_fiat > second_bar.volume_fiat:
            if first_bar.open_price > first_bar.close_price and second_bar.close_price > second_bar.open_price:
                if second_bar.close_price > first_bar.open_price:
                    if first_bar.volume_fiat > get_average_value_of_volume(first_bar.symbol):
                        return True
    return False


def get_all_symbols_with_currency(currency: str = "BUSD") -> list:
    result = []
    for _ in client.get_all_tickers():
        if _["symbol"][-len(currency):] == currency:
            result.append(_["symbol"])
    return result


def create_binance_link(symbol: str) -> str:
    link = f"https://www.binance.com/uk-UA/trade/{symbol[:len(symbol) - 4]}_{symbol[-4:]}?type=spot"
    return link


def main():
    for symbol in get_all_symbols_with_currency():
        symbol_price = client.get_klines(symbol=symbol, interval="1h", limit="3")
        first_bar = create_named_data(symbol, symbol_price[0])
        second_bar = create_named_data(symbol, symbol_price[1])

        if data_comparison(first_bar, second_bar):
            send_text = f"{first_bar},\n {second_bar}\n{create_binance_link(symbol)}"
            send_notification_message(send_text)


def test():
    symbol_price = client.get_klines(symbol="XRPBUSD", interval="5m", limit="3")
    first_bar = create_named_data("XRPBUSD", symbol_price[0])
    second_bar = create_named_data("XRPBUSD", symbol_price[1])
    print(first_bar, second_bar)
    if data_comparison(first_bar, second_bar):
        print(first_bar, second_bar)


def bet(bank: Decimal, bar: BarInfo) -> Decimal:
    crypto_count = Decimal(bank / bar.open_price)
    return Decimal(crypto_count * bar.close_price)


def bar_test():
    bank = decimal.Decimal(50)
    symbol_price = client.get_historical_klines("XRPUSDT", Client.KLINE_INTERVAL_5MINUTE, "1 May, 2018")
    map_symbol_price = tuple(map(lambda item: create_named_data("XRPUSDT", item), symbol_price))
    for num, bar in (enumerate(map_symbol_price[2:])):
        prev_bar: BarInfo = map_symbol_price[num - 1]
        if bar.close_price < bar.open_price and prev_bar.close_price < prev_bar.open_price:
            if prev_bar.volume_fiat > bar.volume_fiat:
                if find_pattern(map_symbol_price[num - 2]):
                    bank = bet(bank, map_symbol_price[num + 1])
                    print(bank)
    print(f"Final bank = {bank}")


def get_historical_data():
    symbol_price = client.get_historical_klines("ADAUSDT", Client.KLINE_INTERVAL_5MINUTE, "1 May, 2018")
    with open("ada_5min.json", "w") as my_file:
        data = json.dumps(symbol_price, indent=4)
        my_file.write(data)


def load_data():
    with open("ada_5min.json", "r") as my_file:
        return json.loads(my_file.read())


def find_pattern(bars: tuple) -> bool:
    if bars[0].open_price < bars[0].close_price:
        if bars[1].open_price > bars[1].close_price and bars[2].open_price > bars[2].close_price:
            return bars[1].volume_fiat > bars[2].volume_fiat
    return False


def get_max_position_available():
    to_use = Decimal(client.get_asset_balance(asset=STABLE_NAME).get('free'))
    price = Decimal(client.get_symbol_ticker(symbol=SYMBOL_NAME).get('price'))
    decide_position_to_use = to_use / price
    return decide_position_to_use * Decimal(0.9995)


def buy_coins():
    qa = get_max_position_available().quantize(Decimal('.01'), rounding=decimal.ROUND_DOWN)
    try:
        client.order_market_buy(
            symbol=SYMBOL_NAME,
            quantity=qa)
        print(f"buy {qa} ADA")
    except BinanceAPIException as BAPIE:
        print(BAPIE)
        if BAPIE.message == "Account has insufficient balance for requested action.":
            buy_coins()
            print("another buy")
    except Exception as e:
        print(e)
        send_notification_message(e)


def sell_coins():
    qa = Decimal(client.get_asset_balance(asset="ADA").get("free")).quantize(Decimal('.01'),
                                                                             rounding=decimal.ROUND_DOWN)
    print(qa)
    try:
        client.order_market_sell(
            symbol='ADAUSDT',
            quantity=qa)
        print(f"sell {qa} coins")
    except Exception as e:
        print(e)
        send_notification_message(e)


def bot():
    if Decimal(client.get_asset_balance(asset="ADA").get("free")) < Decimal(0.2) and Decimal(
            client.get_asset_balance(asset="USDT").get("free")) < Decimal(10):
        return
    if Decimal(client.get_asset_balance(asset="ADA").get("free")) > Decimal(0.2):
        print("try to sell")
        sell_coins()
        print(f"bank after sell - {client.get_asset_balance(asset='USDT').get('free')}")
    symbol_price = client.get_klines(symbol=SYMBOL_NAME, interval="5m", limit="4")
    map_symbol_price = tuple(map(lambda item: create_named_data(SYMBOL_NAME, item), symbol_price))
    if find_pattern(map_symbol_price):
        print("try to buy")
        buy_coins()
        time.sleep(1.46)
        print("sell after 1.5 m")
        sell_coins()
        print(f"bank after sell - {client.get_asset_balance(asset='USDT').get('free')}")


if __name__ == "__main__":
    bot()
