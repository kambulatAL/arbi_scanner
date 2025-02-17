# Crypto Arbitrage Scanner

This Python script scans for arbitrage opportunities between several cryptocurrency exchanges (ByBit, KuCoin, Huobi, BingX, Bitget, MEXC). It fetches market data (bid/ask prices, volumes) and coin information (deposit/withdrawal chains) to identify and display potential arbitrage trades.  The application uses PyQt6 for a simple GUI.

## Features

* **Real-time Data:** Fetches market data from multiple exchanges.
* **Arbitrage Calculation:** Calculates the spread between exchanges and identifies potential arbitrage opportunities.
* **Order Book Analysis:** Calculates the average price based on the top 5 levels of the order book for more accurate arbitrage calculations.
* **Coin Information:** Retrieves deposit and withdrawal chain information for each coin.
* **GUI:** A simple PyQt6 based GUI for selecting exchanges and displaying results.
* **Asynchronous Operations:** Uses `asyncio` and `aiohttp` for efficient and non-blocking network requests.
* **Configuration:** Uses `.env` file for storing API keys for security.

## Requirements

* Python 3.10+
* `pybit`
* `pandas`
* `asyncio`
* `aiohttp`
* `qasync`
* `PyQt6`
* `python-dotenv`

You can install these packages using pip:

```bash
pip install -r requirements.txt
