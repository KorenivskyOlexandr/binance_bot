from binance.client import Client
from constant import binance_api_key, binance_api_secret_key
from decimal import Decimal
from binance_bot import send_notification_message

client = Client(binance_api_key, binance_api_secret_key)


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


def data_comparison(first_bar: BarInfo, second_bar: BarInfo) -> bool:
    if first_bar.volume_fiat > second_bar.volume_fiat:
        if first_bar.open_price > first_bar.close_price:
            if second_bar.close_price > first_bar.open_price:
                return True
    return False


def get_all_symbols_with_currency(currency: str = "BUSD") -> list:
    result = []
    for _ in client.get_all_tickers():
        if _["symbol"][-len(currency):] == currency:
            result.append(_["symbol"])
    return result


def main():
    for symbol in get_all_symbols_with_currency():
        symbol_price = client.get_klines(symbol=symbol, interval="1h", limit="3")
        first_bar = create_named_data(symbol, symbol_price[0])
        second_bar = create_named_data(symbol, symbol_price[1])

        if data_comparison(first_bar, second_bar):
            send_text = f"{first_bar},\n {second_bar}"
            send_notification_message(send_text)


def test():
    symbol_price = client.get_klines(symbol="XRPBUSD", interval="5m", limit="3")
    first_bar = create_named_data("XRPBUSD", symbol_price[0])
    second_bar = create_named_data("XRPBUSD", symbol_price[1])
    if data_comparison(first_bar, second_bar):
        print(first_bar, second_bar)


if __name__ == "__main__":
    main()
