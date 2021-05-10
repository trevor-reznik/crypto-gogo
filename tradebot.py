#
# ─────────────────────────────────────────────────────────────── REFERENCES ─────
#
# Extended Description of Each Method:
# https://cryptocurrenciesstocks.readthedocs.io/kraken.html
# 
# "Crypto Currencies Stock" (CSS) Python Module Docs:
# https://cryptocurrenciesstocks.readthedocs.io/index.html
#
# How to Maintain a Valid Order Book:
# https://support.kraken.com/hc/en-us/articles/360027821131-How-to-maintain-a-valid-order-book-
# 
# Kraken Docs (abridged):
# https://docs.kraken.com/rest/#operation/getTickerInformation
# 
# What is a Nonce Window:
# https://support.kraken.com/hc/en-us/articles/360001148023-What-is-a-nonce-window-
# 
#
# ────────────────────────────────────────────────────────────────────────────────
#

import time
import json, urllib.request
import os
import urllib.parse
import hashlib
import hmac
import base64
import requests


#
# ─────────────────────────────────────────────────────────── PUBLIC METHODS ─────
#
# Server Time, System Status, Asset Info, Tradeable Asset Pairs, Ticker Information,
# OHLC Data, Order Book, Recent Trades, Recent Spreads
#


def asset_info(coin=False):
    """
    For the param currency or for every tradeable asset (if no args), 
    return dict containing:
    aclass           : asset class
    altname          : alternative name
    decimals         : scaling decimal places for record keeping
    display_decimals : scaling decimal places for output display
    """

    res = requests.get('https://api.kraken.com/0/public/Assets')
    if coin:
        return (res.json())["result"][coin]
    return res.json()["result"]


def asset_pair(coin, refcoin):
    """
    Returns dict containing
    altname	            : alternate pair name
    aclass_base	        : asset class of base component
    base	            : asset id of base component
    aclass_quote	    : asset class of quote component
    quote	            : asset id of quote component
    lot	                : volume lot size
    pair_decimals	    : scaling decimal places for pair
    lot_decimals	    : scaling decimal places for volume
    lot_multiplier	    : amount to multiply lot volume by to get currency volume
    leverage_buy	    : array of leverage amounts available when buying
    leverage_sell	    : array of leverage amounts available when selling
    fees	            : fee schedule array in [volume, percent fee] tuples
    fees_maker	        : maker fee schedule array in [volume, percent fee] tuples (if on maker/taker)
    fee_volume_currency : volume discount currency
    margin_call	        : margin call level
    margin_stop         : stop-out/liquidation margin level
    """

    url = 'https://api.kraken.com/0/public/AssetPairs?pair={}{}'.format(coin, refcoin)
    res = requests.get(url)

    return res.json()["result"][coin + refcoin]


def get_order_book(coin, refcoin):
    """
    Returns dic containing 'asks' and 'bids' items.
    'asks' and 'bids' are lists of orders. 
    orders are 3-item lists containing:
    [price, volume, timestamp]
    """

    url = 'https://api.kraken.com/0/public/Depth?pair={}{}'.format(coin, refcoin)
    res = requests.get(url)

    return res.json()["result"][coin + refcoin]


def get_ticker(coin, refcoin):
    """
    Returns 'coin' vs 'refcoin' dict containing:
    a	:   ask array(price, whole lot volume, lot volume)
    b	:   bid array(price, whole lot volume, lot volume)
    c	:   last trade closed array(price, lot volume)
    v	:   volume array(today, last 24 hours),
    p	:   volume weighted average price array(today, last 24 hours)
    t	:   number of trades array(today, last 24 hours)
    l	:   low array(today, last 24 hours)
    h	:   high array(today, last 24 hours)
    o	:   today’s opening price
    """

    url = "https://api.kraken.com/0/public/Ticker?pair={}{}"
    res = requests.get(url.format(coin, refcoin))

    return res.json()["result"][coin + refcoin]


def get_price(coin, refcoin):
    """
    Returns 'coin' vs 'refcoin' price based on
    price of last closed order 
    """
    
    url = "https://api.kraken.com/0/public/Ticker?pair={}{}"
    res = requests.get(url.format(coin, refcoin))

    return res.json()["result"][coin + refcoin]["c"][0]




# ──────────────────────────────────────────────────── AUTHENTICATED METHODS ─────
#
# USER DATA: Closed Orders, Orders Info, Trades History, Trades Info, Open Positions,
#            Ledgers Info, Ledgers, Trade Volume, Export Report, Export Report Status,
#            Retrieve Data Export, Delete Export Report 
# 
# USER TRADING: Add Order, Cancel Order, Cancel All Orders, Cancel All Orders After X
#
# USER FUNDING: Deposit Methods, Deposit Addresses, Status of Recent Deposits,
#               Withdrawal Information, Withdraw Funds, Get Status of Recent Winthdrawals,
#               Request Withdrawal Cancellation, Request Wallet Transfer
#
# 


public_key = os.environ.get("KRAK_KEY")
private_key = os.environ.get("KRAK_SEC")
api_url = "https://api.kraken.com"


def get_kraken_signature(urlpath, data, secret):

    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()


def kraken_request(uri_path, data, api_key, api_sec):
    """
    Attaches auth headers and returns results of a POST request
    """

    headers = {
        "API-Key" : api_key,
        "API-Sign" : get_kraken_signature(uri_path, data, api_sec)
    }             
    req = requests.post((api_url + uri_path), headers=headers, data=data)
    
    return req


def usr_fees(coin, refcoin):
    """
    Result dict contains: currency, volume, fees, fees_maker.
        fees and fees_maker contain:
            coin+refcoin:
                fee
                minfee
                maxfee
                nextfee
                nextvolume
                tiervolume

    Note: If an asset pair is on a maker/taker fee schedule, 
    the taker side is given in fees and maker side in 
    fees_maker. For pairs not on maker/taker, they will
    only be given in fees.
    """

    data = {
        "nonce": str(int(1000*time.time())),
        "fee-info": True,
        "pair": coin.upper() + refcoin.upper()
    }

    res = kraken_request(
        "/0/private/TradeVolume",
        data,
        public_key,
        private_key
    )

    res_layer = res.json()["result"]
    first_currency_keyname = list(res_layer["fees"])[0]
    f = res_layer["fees"][first_currency_keyname]["fee"]

    return float(f)

     
def balance(coin="all"):
    """
    Result dict contains balances of all owned currencies
    """

    data = {
        "nonce": str(int(1000*time.time())),
    }

    res = kraken_request(
        "/0/private/Balance",
        data,
        public_key,
        private_key
    )

    if coin != "all":
        return res.json()["result"][coin.upper()]
    return res.json()["result"]
