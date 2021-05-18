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
###      ──────────────────────────────────────────────────── AUTHENTICATED METHODS ─────
###      |                                                                              |
###      |     USER DATA: Closed Orders, Orders Info, Trades History,                   |   
###      |                Trades Info, Open Positions, Ledgers Info, Ledgers,           |   
###      |                Trade Volume, Export Report, Export Report Status,            |   
###      |                Retrieve Data Export, Delete Export Report                    | 
###      |                                                                              |   
###      |  USER TRADING: Add Order, Cancel Order, Cancel All Orders,                   |   
###      |                Cancel All Orders After X                                     |   
###      |                                                                              |
###      |  USER FUNDING: Deposit Methods, Deposit Addresses,                           |   
###      |                Status of Recent Deposits,                                    |
###      |                Withdrawal Information, Withdraw Funds,                       |
###      |                Get Status of Recent Winthdrawals,                            | 
###      |                Request Withdrawal Cancellation,                              |
###      |                Request Wallet Transfer                                       |
###      |                                                                              |
###      |          DOCS: https://docs.kraken.com/rest/
###      ────────────────────────────────────────────────────────────────────────────────
###
###


import hashlib, hmac, base64
import urllib.request, urllib.parse
import os, time
import requests


try:
    public_key = os.environ.get("KRAK_KEY")
    private_key = os.environ.get("KRAK_SEC")
    api_url = "https://api.kraken.com"
except:
    public_key = input("Enter Kraken API Public Key:\n")
    private_key = input("Enter Kraken API Secret:\n")
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


def usr_fees(pair):
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
        "pair": pair.upper()
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


def trade_history(verbose=False):
    """
    Optional Data Params:
        type    : all | any position | closed position
        trades  : false | true
                   (whether or not to include trades related
                   to position)
        start   : Starting unix timestamp or trade tx ID of results 
        end     : Ending unix timestamp or trade tx ID of results 
        ofs     : Result offset for pagination

    Result dict containing:
    trades
        $trade-ID
            ordertxid   : order id
            postxid     : post id
            pair        : currency pair
            time        : time initiated
            type        : buy | sell
            ordertype   : limit | market | etc.
            price       : coin / ref coin
            cost        : nominal cost in ref coin
            fee         : nominal fee in ref coin
            vol         : # of coin
            margin      : margin float
            misc        : ...

    Note: Unless otherwise stated, costs, fees, prices, and volumes 
          are specified with the precision for the asset pair (pair_decimals
          and lot_decimals), not the individual assets' precision (decimals).
    """

    data = {
        "nonce": str(int(1000*time.time())),
        "trades": True
    }

    res = kraken_request(
        "/0/private/TradesHistory",
        data,
        public_key,
        private_key
    )

    if verbose:
        for order_id, trade in res.json()["result"]["trades"].items():
            print("Order ID:", order_id)
            for x, y in trade.items():
                print(x + ":", y)
            print()

    return res.json()["result"]["trades"]


def add_order(pair, order_direction, volume, price="NOT LIMIT", order_type="limit", just_test=False):
    """
    Params:
        pair            : trading pair abbreviation
        order_direction : "buy" or "sell"
        volume          : Order quantity in terms of the base asset
        price           : Limit price for limit orders. Leave default for market orders
        order_type      : "market" "limit" "stop-loss" "take-profit" "stop-loss-limit" "take-profit-limit" "settle-position"
        just_test       : For testing -- validate order but don't execute


    Returns:
        error:
            error message if error
        result:
            descr:
                order : [$type, $volume, $pair @ $limit-price with $leverage],
                close : [conditional close position @ stop loss $stop-loss-price -> limit $limit-price ]
            txid:
                order ID

    GET Params:
        nonce       : Nonce used in construction of API-Sign header
        ordertype   : "market" "limit" "stop-loss" "take-profit" "stop-loss-limit" "take-profit-limit" "settle-position"
        type        : "buy" "sell"
        volume	    : [optional] Order quantity in terms of the base asset
                        Note: Volume can be specified as 0 for closing margin orders to automatically 
                        fill the requisite quantity.
        pair        : Asset pair id or altname
        price	    : Limit price for limit orders
                      Trigger price for stop-loss, stop-loss-limit, take-profit and take-profit-limit orders
        price2	    : Limit price for stop-loss-limit and take-profit-limit orders
                        Note: Either price or price2 can be preceded by +, -, or # to specify the order 
                              price as an offset relative to the last traded price. + adds the amount to, 
                              and - subtracts the amount from the last traded price. # will either add or 
                              subtract the amount to the last traded price, depending on the direction and 
                              order type used. Relative prices can be suffixed with a % to signify the 
                              relative amount as a percentage.

        leverage	: [optional] Amount of leverage desired (default = none)
        oflags      : [optional] Comma delimited list of order flags
                        post post-only order (available when ordertype = limit)
                        fcib prefer fee in base currency (default if selling)
                        fciq prefer fee in quote currency (default if buying, mutually exclusive with fcib)
                        nompp disable market price protection for market orders
        starttm	    : [optional] Scheduled start time. Can be specified as an absolute timestamp or as a number of seconds in the future.
                        0 now (default)
                        +<n> schedule start time seconds from now
                        <n> = unix timestamp of start time
        expiretm    : [optional]	
        close       :
            [ordertype] : Conditional close order type.
                            "limit" "stop-loss" "take-profit" "stop-loss-limit" "take-profit-limit"
                            Note: Conditional close orders are triggered by execution of the primary 
                                  order in the same quantity and opposite direction, but once triggered
                                  are independent orders that may reduce or increase net position.
            [price]	    : Conditional close order price
            [price2]	: Conditional close order price2
        validate    : [boolean]
                      Default: false
                      Validate inputs only. Do not submit order.
    """

    if price == "NOT LIMIT":
        data = {
            "nonce": str(int(1000*time.time())),
            "ordertype": order_type,
            "type": order_direction,
            "volume": float(volume),
            "pair" : pair
        }
    else:
        data = {
            "nonce": str(int(1000*time.time())),
            "ordertype": order_type,
            "type": order_direction,
            "volume": float(volume),
            "pair" : pair,
            "price": float(price)
        }

    if just_test:
        data["validate"] = True

    res = kraken_request(
        "/0/private/AddOrder",
        data,
        public_key,
        private_key
    )

    return res.json()