###    
###                                                                        
###   oooo    oooo                    oooo                                     .o.       ooooooooo.   ooooo 
###   `888   .8P'                     `888                                    .888.      `888   `Y88. `888' 
###    888  d8'    oooo d8b  .oooo.    888  oooo   .ooooo.  ooo. .oo.        .8"888.      888   .d88'  888  
###    88888[      `888""8P `P  )88b   888 .8P'   d88' `88b `888P"Y88b      .8' `888.     888ooo88P'   888  
###    888`88b.     888      .oP"888   888888.    888ooo888  888   888     .88ooo8888.    888          888  
###    888  `88b.   888     d8(  888   888 `88b.  888    .o  888   888    .8'     `888.   888          888  
###   o888o  o888o d888b    `Y888""8o o888o o888o `Y8bod8P' o888o o888o  o88o     o8888o o888o        o888o 
###
###
###                                                                
###      ──────────────────────────────────────────────────────── PUBLIC METHODS ─────
###      |                                                                           |
###      | Server Time, System Status, Asset Info, Tradeable Asset Pairs,            |
###      | Ticker Information, OHLC Data, Order Book, Recent Trades, Recent Spreads  |
###      |                                                                           |
###      | Docs: https://cryptocurrenciesstocks.readthedocs.io/kraken.html           |
###      |                                                                           |
###      ─────────────────────────────────────────────────────────────────────────────  
###
###
###         



import requests


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


def asset_pair(pair):
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

    url = 'https://api.kraken.com/0/public/AssetPairs?pair={}'.format(pair)
    res = requests.get(url)

    return res.json()["result"][pair]


def all_asset_pairs():
    """
    Returns dict of every tradeable assets pair containing
    """
    res = requests.get("https://api.kraken.com/0/public/AssetPairs")

    return res.json()["result"]


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


def get_price(pair):
    """
    Returns price against reference currency based on 
    price of last closed order in market
    """

    if type(pair) == list:
        pair = pair[0] + pair[1]
    
    url = "https://api.kraken.com/0/public/Ticker?pair={}".format(pair)
    res = requests.get(url)

    return float(res.json()["result"][pair]["c"][0])
