import sys
from pybit.unified_trading import HTTP
import pandas as pd
import asyncio
import aiohttp
from qasync import QEventLoop
from dotenv import dotenv_values

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import QTimer

import time
import hmac
from hashlib import sha256


BYBIT_TICKER_URL    = "https://api.bybit.com/v5/market/tickers?category=spot"
HUOBI_TICKER_URL    = "https://api.huobi.pro/market/tickers"
KUCOIN_TICKER_URL   = "https://api.kucoin.com/api/v1/market/allTickers"
BINGX_TICKER_URL    = "https://open-api.bingx.com/openApi/spot/v1/ticker/24hr?"
BITGET_TICKER_URL   = "https://api.bitget.com/api/v2/spot/market/tickers"
MEXC_TICKER_URL     = "https://api.mexc.com/api/v3/ticker/24hr"


BYBIT_ORDERBOOK_URL     = "https://api.bybit.com/v5/market/orderbook?category=spot&limit=5&symbol="
HOUBI_ORDERBOOK_URL     = "https://api.huobi.pro/market/depth?depth=5&type=step1&symbol="
KUCOIN_ORDERBOOK_URL    = "https://api.kucoin.com/api/v1/market/orderbook/level2_20?symbol="
BINGX_ORDERBOOK_URL     = "https://open-api.bingx.com/openApi/spot/v1/market/depth?limit=5&symbol="
BITGET_ORDERBOOK_URL    = "https://api.bitget.com/api/v2/spot/market/orderbook?type=step1&limit=5&symbol="
MEXC_ORDERBOOK_URL      = "https://api.mexc.com/api/v3/depth?limit=5&symbol="

KUCOIN_COIN_INFO_URL    = "https://api.kucoin.com/api/v2/currencies/"
HUOBI_COIN_INFO_URL     = "https://api.huobi.pro/v2/reference/currencies?currency="
BINGX_COIN_INFO_URL     = "https://open-api.bingx.com/openApi/wallets/v1/capital/config/getall"
BITGET_COIN_INFO_URL    = "https://api.bitget.com/api/v2/spot/public/coins?coin="
MEXC_COIN_INFO_URL      = "https://api.mexc.com/api/v3/capital/config/getall"


config = dotenv_values()

BYBIT_API_KEY = config['BYBIT_API_KEY']
BYBIT_SECRET_KEY = config['BYBIT_SECRET_KEY']
BINGX_API_KEY = config['BINGX_API_KEY']
BINGX_SECRET_KEY = config['BINGX_SECRET_KEY']
MEXC_API_KEY = config['MEXC_API_KEY']
MEXC_SECRET_KEY = config['MEXC_SECRET_KEY']


class Scanner:
    """
    A class to handle data extraction from various cryptocurrency exchanges (ByBit, KuCoin, Huobi, BingX, Bitget).
    Provides methods to fetch market data, coin information, and calculate arbitrage spreads.
    """
        
    def get_bybit_data(self, response):
        """
        Extracts and formats market data from a ByBit API response.

        Args:
            response (dict): The ByBit API response in JSON format.

        Returns:
            dict: A dictionary where the keys are symbols (e.g., "BTC/USDT") and values are tuples with last price and volume.
        """
        return {d["symbol"].replace("USDT", "/USDT"): (float(d["bid1Price"]), float(d['ask1Price']), round(float(d["turnover24h"]), 1)) 
            for d in response['result']['list']}


    def get_kucoin_data(self, response):
        """
        Extracts and formats market data from a KuCoin API response.

        Args:
            response (dict): The KuCoin API response in JSON format.

        Returns:
            dict: A dictionary where the keys are symbols (e.g., "BTC/USDT") and values are tuples with bid/ask and volume.
        """

        return {d["symbol"].replace("-", "/"): (float(d["buy"]), float(d['sell']), round(float(d["volValue"]), 1)) 
            for d in response["data"]["ticker"]}
    

    def get_huobi_data(self, response):
        """
        Extracts and formats market data from a Huobi API response.

        Args:
            response (dict): The Huobi API response in JSON format.

        Returns:
            dict: A dictionary where the keys are symbols (e.g., "BTC/USDT") and values are tuples with bid/ask and volume.
        """
        return {d["symbol"].upper().replace("USDT", "/USDT"): (float(d["bid"]), float(d['ask']), round(float(d["vol"]), 1)) 
            for d in response["data"]}

        
    def get_bingx_data(self, response):
        """
        Extracts and formats market data from a BingX API response.

        Args:
            response (dict): The BingX API response in JSON format.

        Returns:
            dict: A dictionary where the keys are symbols (e.g., "BTC/USDT") and values are tuples with last price and volume.
        """

        return {d["symbol"].replace("-", "/"): (float(d["bidPrice"]) if 'bidPrice' in d.keys() else None, 
                                                float(d['askPrice']) if 'askPrice' in d.keys() else None, 
                                                round(float(d["quoteVolume"]), 1)) 
                for d in response['data']}


    def get_bitget_data(self, response):
        """
        Extracts and formats market data from a Bitget API response.

        Args:
            response (dict): The Bitget API response in JSON format.

        Returns:
            dict: A dictionary where the keys are symbols (e.g., "BTC/USDT") and values are tuples with last price and volume.
        """
        return { d["symbol"].upper().replace("USDT", "/USDT"): (float(d['bidPr']), float(d['askPr']), round(float(d['usdtVolume']), 1)) 
            for d in response['data']}


    def get_mexc_data(self, response):
        return { d["symbol"].replace("USDT", "/USDT"): (float(d['bidPrice']), float(d['askPrice']), round(float(d['quoteVolume']), 1)) 
            for d in response}


    async def bybit_session_coin(self, coin):
        """
        Asynchronously fetches coin information from ByBit API.

        Args:
            coin (str): The coin symbol to fetch information for.

        Returns:
            dict: The ByBit API response containing coin information.
        """
        session = HTTP(
            api_key=BYBIT_API_KEY,
            api_secret=BYBIT_SECRET_KEY
        )
        return await asyncio.to_thread(session.get_coin_info, coin=coin)

    
    async def get_bybit_coin_info(self, coin):
        """
        Asynchronously fetches and processes coin information from ByBit API.

        Args:
            coin (str): The coin symbol to fetch information for.

        Returns:
            tuple: Two lists of strings representing deposit and withdrawal chain types.
        """
        response = await self.bybit_session_coin(coin)
        response = response['result']['rows']
        if response:
            response = response[0]
        else:
            return [], []

        chain_deposit_list, chain_withdraw_list = [], []

        for chain in response['chains']:
            if chain['chainDeposit'] == '1':
                chain_deposit_list.append(f"{chain['chain']}({chain['chainType']})")
            if chain['chainWithdraw'] == '1':
                chain_withdraw_list.append(f"{chain['chain']}({chain['chainType']})")
        return chain_deposit_list, chain_withdraw_list


    async def get_kucoin_coin_info(self, coin):
        """
        Asynchronously fetches and processes coin information from KuCoin API.

        Args:
            coin (str): The coin symbol to fetch information for.

        Returns:
            tuple: Two lists of strings representing deposit and withdrawal chain types.
        """
        response = ''
        async with aiohttp.ClientSession() as session:
            async with session.get(KUCOIN_COIN_INFO_URL + coin) as resp:
                response =  await resp.json()

        response = response['data']
        chain_deposit_list, chain_withdraw_list = [], []
        
        for chain in response['chains']:
            if chain['isDepositEnabled'] == True:
                chain_deposit_list.append(f"{chain['chain']}({chain['chainName']})")
            if chain['isWithdrawEnabled'] == True:
                chain_withdraw_list.append(f"{chain['chain']}({chain['chainName']})")
        return chain_deposit_list, chain_withdraw_list
    

    async def get_huobi_coin_info(self, coin):
        """
        Asynchronously fetches and processes coin information from Huobi API.

        Args:
            coin (str): The coin symbol to fetch information for.

        Returns:
            tuple: Two lists of strings representing deposit and withdrawal chain types.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(HUOBI_COIN_INFO_URL + coin.lower()) as resp:
                response =  await resp.json()
        
        response = response['data'][0]
        chain_deposit_list, chain_withdraw_list = [], []
        
        for chain in response['chains']:
            if chain['depositStatus'] == 'allowed':
                chain_deposit_list.append(f"{chain['chain']}({chain['fullName']})")
            if chain['withdrawStatus'] == 'allowed':
                chain_withdraw_list.append(f"{chain['chain']}({chain['fullName']})")
        return chain_deposit_list, chain_withdraw_list


    @staticmethod
    async def load_bingx_coins_info(coin):
        """
        Loads coin information from BingX API, including signing the request.

        Args:
            coin (str): The coin symbol to fetch information for.

        Returns:
            dict: The BingX API response containing coin information.
        """
        response = ''
        timestamp = str(int(time.time() * 1000))
        recvWindow = "5000"

        params = "timestamp=%s&recvWindow=%s&coin=%s"%(timestamp, recvWindow, coin)
        signature = hmac.new(BINGX_SECRET_KEY.encode(), params.encode(), digestmod=sha256).hexdigest()
        url = f"{BINGX_COIN_INFO_URL}?{params}&signature={signature}"
        
        headers = {
            'X-BX-APIKEY': BINGX_API_KEY,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                response = await resp.json()

        return response


    async def get_bingx_coin_info(self, coin):
        """
        Asynchronously fetches and processes coin information from BingX API.

        Args:
            coin (str): The coin symbol to fetch information for.

        Returns:
            tuple: Two lists of strings representing deposit and withdrawal network types.
        """
        response = await self.load_bingx_coins_info(coin)
        try:
            response = response['data'][0]['networkList']
        except:
            return [], []

        chain_deposit_list, chain_withdraw_list = [], []

        for chain in response:
            if chain['depositEnable'] == True:
                chain_deposit_list.append(f"{chain['name']}({chain['network']})")
            if chain['withdrawEnable'] == True:
                chain_withdraw_list.append(f"{chain['name']}({chain['network']})")
        await asyncio.sleep(1)
        return chain_deposit_list, chain_withdraw_list 
    

    async def get_bitget_coin_info(self, coin):
        """
        Asynchronously fetches and processes coin information from Bitget API.

        Args:
            coin (str): The coin symbol to fetch information for.

        Returns:
            tuple: Two lists of strings representing deposit and withdrawal chain types.
        """
        response = ''
        async with aiohttp.ClientSession() as session:
            async with session.get(BITGET_COIN_INFO_URL + coin) as resp:
                response =  await resp.json()
        
        response = response['data']

        if response:
            response = response[0]
        else:
            return [], []

        chain_deposit_list, chain_withdraw_list = [], []
        for chain in response['chains']:
            if chain['rechargeable'] == 'true':
                chain_deposit_list.append(chain['chain'])
            if chain['withdrawable'] == 'true':
                chain_withdraw_list.append(chain['chain'])
        return chain_deposit_list, chain_withdraw_list


    @staticmethod
    async def load_mexc_coins_info():        
        response = ''
        timestamp = str(int(time.time() * 1000))

        params = "timestamp=%s"%(timestamp)
        signature = hmac.new(MEXC_SECRET_KEY.encode(), params.encode(), digestmod=sha256).hexdigest()
        url = f"{MEXC_COIN_INFO_URL}?{params}&signature={signature}"
        
        headers = {
            'X-MEXC-APIKEY': MEXC_API_KEY,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                response = await resp.json()

        return response


    async def get_mexc_coin_info(self, coin):
    
        response = await self.load_mexc_coins_info()
        response = [d for d in response if d['coin'] == coin]

        try:
            response = response[0]['networkList']
        except:
            return [], []

        chain_deposit_list, chain_withdraw_list = [], []
        for chain in response:
            if chain['depositEnable'] == True:
                chain_deposit_list.append(chain['network'])
            if chain['withdrawEnable'] == True:
                chain_withdraw_list.append(chain['network'])
        # await asyncio.sleep(1)
        return chain_deposit_list, chain_withdraw_list 


    async def get_coins_info(self, coins, exch_name):
        """
        Retrieves deposit and withdrawal chain information for a list of coins from a specified exchange.

        Args:
            coins (list): A list of coin symbols.
            exch_name (str): The exchange name (e.g., 'ByBit', 'KuCoin').

        Returns:
            tuple: Two lists of strings representing deposit and withdrawal chain types.
        """
        coins_dep_list, coins_withdr_list = [], []
        
        for coin in coins:
            deposit_allowance, withdraw_allowance = await getattr(self, f'get_{exch_name.lower()}_coin_info')(coin)
            coins_dep_list.append(', '.join(deposit_allowance))
            coins_withdr_list.append(', '.join(withdraw_allowance))

        return coins_dep_list, coins_withdr_list


    @staticmethod
    def get_avg_price_top_5(order_book):
        """
       Calculates the average price taking into account the volumes at the first 5 levels of the stack.
        
        :param order_book: List of stack levels [[price, volume], [price, volume], ...].
        :return: Average price including volumes.
        """
        total_volume = 0
        total_cost = 0
        
        for price, volume in order_book:  
            total_cost += float(price) * float(volume) 
            total_volume += float(volume) 
        
        if total_volume == 0:
            return None, None 
        
        return round(total_cost / total_volume, 5), round(total_volume, 2)


    async def get_bybit_orderbook(self, coin, buy):
        pair = coin + "USDT"
        async with aiohttp.ClientSession() as session:
            async with session.get(BYBIT_ORDERBOOK_URL + pair) as resp:
                response =  await resp.json()
        
        response = response['result']
        return self.get_avg_price_top_5(response['a']) if buy else self.get_avg_price_top_5(response['b'])
    

    async def get_huobi_orderbook(self, coin, buy):
        pair = coin.lower() + "usdt"
        async with aiohttp.ClientSession() as session:
            async with session.get(HOUBI_ORDERBOOK_URL + pair) as resp:
                response =  await resp.json()
        
        response = response['tick']
        return self.get_avg_price_top_5(response['asks']) if buy else self.get_avg_price_top_5(response['bids'])
    

    async def get_kucoin_orderbook(self, coin, buy):
        pair = coin + '-USDT'

        async with aiohttp.ClientSession() as session:
            async with session.get(KUCOIN_ORDERBOOK_URL + pair) as resp:
                response =  await resp.json()
        
        response = response['data']
        return self.get_avg_price_top_5(response['asks']) if buy else self.get_avg_price_top_5(response['bids'])


    async def get_bingx_orderbook(self, coin, buy):
        pair = coin + '-USDT'
        params = {'timestamp': str(int(time.time() * 1000))}
        async with aiohttp.ClientSession() as session:
            async with session.get(BINGX_ORDERBOOK_URL + pair, params=params) as resp:
                response =  await resp.json()
        
        response = response['data']
        return self.get_avg_price_top_5(response['asks']) if buy else self.get_avg_price_top_5(response['bids'])


    async def get_bitget_orderbook(self, coin, buy):
        pair = coin + 'USDT'
        async with aiohttp.ClientSession() as session:
            async with session.get(BITGET_ORDERBOOK_URL + pair) as resp:
                response =  await resp.json()
        
        response = response['data']
        return self.get_avg_price_top_5(response['asks']) if buy else self.get_avg_price_top_5(response['bids'])


    async def get_mexc_orderbook(self, coin, buy):
        pair = coin + 'USDT'
        async with aiohttp.ClientSession() as session:
            async with session.get(MEXC_ORDERBOOK_URL + pair) as resp:
                response =  await resp.json()
        
        # response = response['data']
        return self.get_avg_price_top_5(response['asks']) if buy else self.get_avg_price_top_5(response['bids'])


    async def calc_orderbook_price(self, exch, coin, buy=False):
        return await getattr(self, f"get_{exch.lower()}_orderbook")(coin.split('/')[0], buy)
        

    @staticmethod
    def calculate_spread(exch1, exch2, bid1, ask1, bid2, ask2):
        spread_buy = (bid2 - ask1) / (ask1+0.0001) * 100  # buy on exch 1, sell on exch 2
        spread_sell = (bid1 - ask2) / (ask2+0.0001) * 100  # buy on exch 2, sell on exch 1

        if spread_buy > spread_sell:
            best_spread = spread_buy
            buy_exchange, sell_exchange = exch1, exch2
        else:
            best_spread = spread_sell
            buy_exchange, sell_exchange = exch2, exch1

        return round(best_spread, 2), buy_exchange, sell_exchange


    async def get_spread_data(self, data1, data2, common_symbols, exch_name1, exch_name2):
        """
        Compares the bid prices and volumes between two exchanges, calculates the spread, 
        and filters out results that don't meet the specified criteria.

        Args:
            data1 (dict): Market data from the first exchange.
            data2 (dict): Market data from the second exchange.
            common_symbols (set): A set of common symbols between the two exchanges.
            exch_name1 (str): The name of the first exchange.
            exch_name2 (str): The name of the second exchange.

        Returns:
            pd.DataFrame: A DataFrame with the top 20 arbitrage opportunities, including spread, volume, and chain information.
        """
        data = []

        for symbol in common_symbols:
            bid_exch1, ask_exch1, vol_exch1 = data1.get(symbol, (None, None, None))
            bid_exch2, ask_exch2, vol_exch2 = data2.get(symbol, (None, None, None))

            if None not in (bid_exch1, ask_exch1, bid_exch2, ask_exch2):
                spread, buy_exch, sell_exch = self.calculate_spread(exch_name1, exch_name2, bid_exch1, ask_exch1, bid_exch2, ask_exch2)
                if (spread >= 0.6 and spread <= 35) and (vol_exch1 > 200000 and vol_exch2 > 200000):

                    mean_buy_orderbook_price, buy_amount = await self.calc_orderbook_price(buy_exch, symbol, buy=True)
                    mean_sell_orderbook_price, sell_amount = await self.calc_orderbook_price(sell_exch, symbol, buy=False)

                    data.append([symbol, bid_exch1, ask_exch1, bid_exch2, ask_exch2, spread, 
                                 f'{buy_exch} >> {sell_exch}', mean_buy_orderbook_price, mean_sell_orderbook_price,
                                 buy_amount, sell_amount])

        df = pd.DataFrame(data, columns=[
            "Coin", f"Bid {exch_name1}", f"Ask {exch_name1}", 
            f"Bid {exch_name2}", f"Ask {exch_name2}",
            "Spread (%)", "Buy >> Sell", f"Mean order buy price", f"Mean order sell price",
            f'Buy amount', f'Sell amount'])
        
        df.sort_values(by=['Spread (%)'], ascending=False, inplace=True)
        
        df = df.head(20)
        coins = df['Coin'].str.split('/').str[0].to_list()
        
        exch1_dep_list, exch1_withd_list = await self.get_coins_info(coins, exch_name1)
        df[f'{exch_name1}_deposit_chains'] = exch1_dep_list
        df[f'{exch_name1}_withdraw_chains'] = exch1_withd_list
        
        exch2_dep_list, exch2_withd_list = await self.get_coins_info(coins, exch_name2)
        df[f'{exch_name2}_deposit_chains'] = exch2_dep_list
        df[f'{exch_name2}_withdraw_chains'] = exch2_withd_list

        df.replace("", pd.NA, inplace=True)
        return df.dropna()


class ArbitrageGUI(QWidget):
    """
    A GUI class for displaying arbitrage opportunities between two selected exchanges. 
    Allows users to select exchanges and view the top arbitrage opportunities.
    """
    def __init__(self):
        """
        Initializes the GUI components and starts a timer to periodically update the data.
        """
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_update_data)
        self.timer.start(10000)


    def initUI(self):
        """
        Initializes the user interface with dropdowns for exchange selection, a button to fetch data, 
        and a table to display the results.
        """
        layout = QVBoxLayout()
        self.exchange1 = QComboBox()
        self.exchange2 = QComboBox()
        self.exchange1.addItems(["ByBit", "KuCoin", "Huobi", "BingX", "Bitget", "MEXC"])
        self.exchange2.addItems(["ByBit", "KuCoin", "Huobi", "BingX", "Bitget", "MEXC"])
        self.button = QPushButton("Get data")
        self.button.clicked.connect(self.run_update_data)
        self.table = QTableWidget()
        layout.addWidget(self.exchange1)
        layout.addWidget(self.exchange2)
        layout.addWidget(self.button)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.scanner = Scanner()


    def run_update_data(self):
        """
        Starts the asynchronous data update task.
        """
        asyncio.ensure_future(self.update_data())


    async def update_data(self):
        """
        Fetches and updates the data for the selected exchanges.
        """
        exch1 = self.exchange1.currentText()
        exch2 = self.exchange2.currentText()
        if exch1 == exch2:
            return
        data = await self.fetch_data(exch1, exch2)
        self.populate_table(data)
        

    async def fetch_data(self, exch1, exch2):
        """
        Fetches the market data from the selected exchanges.

        Args:
            exch1 (str): The name of the first exchange.
            exch2 (str): The name of the second exchange.

        Returns:
            pd.DataFrame: A DataFrame with arbitrage opportunities.
        """
        urls = {
            "ByBit": BYBIT_TICKER_URL, "KuCoin": KUCOIN_TICKER_URL,
            "Huobi": HUOBI_TICKER_URL,"BingX": BINGX_TICKER_URL,
            "Bitget": BITGET_TICKER_URL, "MEXC": MEXC_TICKER_URL
        }
        
        params1 = {} if 'BingX' != exch1 else {'timestamp': str(int(time.time() * 1000))}
        params2 = {} if 'BingX' != exch2 else {'timestamp': str(int(time.time() * 1000))}
        response1, response2 = '', ''
        
        async with aiohttp.ClientSession() as session:
            async with session.get(urls[exch1], params=params1) as resp1:
                response1 =  await resp1.json()
            async with session.get(urls[exch2], params=params2) as resp2:
                response2 =  await resp2.json()

        data1 = getattr(self.scanner, f"get_{exch1.lower()}_data")(response1)
        data2 = getattr(self.scanner, f"get_{exch2.lower()}_data")(response2)
        common_symbols = set(data1.keys()).intersection(set(data2.keys()))
        
        return await self.scanner.get_spread_data(data1, data2, common_symbols, exch1, exch2)


    def populate_table(self, df):
        """
        Populates the table with arbitrage data.
        Args:
            df (pd.DataFrame): A DataFrame containing the arbitrage opportunities.
        """
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns)

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                self.table.setItem(row, col, QTableWidgetItem(str(df.iloc[row, col])))

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()


if __name__ == "__main__":
    """
    Initializes the application and runs the event loop.
    """
    app = QApplication(sys.argv)
    loop = QEventLoop(app) 
    asyncio.set_event_loop(loop)
    gui = ArbitrageGUI()
    
    gui.show()
    with loop:
        loop.run_forever()
