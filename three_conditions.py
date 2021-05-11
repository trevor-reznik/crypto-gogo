
# TODO: Calculations foor stop and limit that are informed by the volume/range of the trading pair (along with other analytic ml equations)
# TODO: calling the stop_limit function repeatedly in the order dictionary init function makes individual calls to the private API each time in order to get the user fees amount (might not be bad if this function is only used once)


from tradebot import usr_fees, balance, trade_history, get_price, add_order, asset_pair
import pickle
from termcolor import colored
import time

#
# ────────────────────────────────────────────────── CREATE PRICE THRESHOLDS ─────
#


def stop_limit(trading_pair, refc_cost, asset_balance, stop=False, limit=False, hard_floor=False, fee="use API"):
    """
    Purpose:
        Get price for all three conditions in a dictionary.

    Use:
        If only want floor/ceiling price with given percent, then only use
        the associated values in the returned dict.
        Leave optional params as False in order to use default percentages.

    Returns:
        (1) ceiling_price,
        (2) post_ceiling_price,
        (3) floor_price,
        (4) post_floor_price,
        (5) hard_floor_price

    Params:
        trading_pair    : Kraken abbreviation for the trading pair
        refc_cost       : cost of initial trade in the reference currency
        asset_balance   : volume of trade in the asset (owned/purchased) currency
        stop            : first floor/ceiling that activates the limit condition
        limit           : take-profit/stop-loss that's initiated after 1st condition is met
    """

    ### Calculations:
    ###
    ###        1 REFC           balance in COIN         ( desired percentage * buy-in in REFC )       
    ###    --------------   X   ---------------     =       
    ###    new price COIN              1 
    ###
    ###    
    ###    price = ( desired percentage * buy-in in REFC ) / balance in COIN
    ###

    # ─── DEFAULTS ───────────────────────────────────────────────────────────────────

    if not stop:
        stop = .05
    if not limit:
        limit = float(stop) / 2.0
    if not hard_floor:
        hard_floor = float(stop) * 1.75
    # Get the user fees for this pair (based on fee schedule)
    if fee == "use API":
        fee = ( usr_fees(trading_pair) + .0000009 ) * 2.0
    
    # ─── CONDITION A - CEILING -> LIMIT ─────────────────────────────────────────────

    ceiling_percent = 1.0 + fee + float(stop)
    post_ceiling_percent = 1.0 + fee + float(limit)

    ceiling_price = ( float(refc_cost) * ceiling_percent ) / float(asset_balance)
    post_ceiling_price = ( float(refc_cost) * post_ceiling_percent ) / float(asset_balance)

    # ─── CONDITION B - FLOOR -> LIMIT ───────────────────────────────────────────────

    floor_percent = 1.0 - ( float(stop) * 1.880 )
    post_floor_percent = floor_percent + float(limit)
    
    floor_price = ( float(refc_cost) * floor_percent ) / float(asset_balance)
    post_floor_price = ( float(refc_cost) * post_floor_percent ) / float(asset_balance)

    # ─── CONDITION C - HARD FLOOR ───────────────────────────────────────────────────

    hard_floor_percent = 1.0 - ( float(hard_floor) * 2.750 )

    hard_floor_price = ( float(refc_cost) * hard_floor_percent ) / float(asset_balance)

    # ────────────────────────────────────────────────────────────────────────────────

    return {
        "ceiling" : ceiling_price,
        "post ceiling" :post_ceiling_price,
        "floor" : floor_price,
        "post floor" : post_floor_price,
        "hard floor" : hard_floor_price
    }


#
# ───────────────────────────────────────────────── USING PERSISTENT OBJECTS ─────
#


def save_obj(obj, name):
    """
    Saves an object to a file for persistent use between
    program instances. 
    
    Params:
        obj     : the object to save
        name    : the name of the file to write to/create
    """

    # https://stackoverflow.com/questions/19201290/how-to-save-a-dictionary-to-a-file

    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    """
    Returns an object that was previously saved with the
    save_obj() function. 
    
    This Program's Stored Objects:
        order   : the dictionary of orders and floor/ceiling prices

    Params:
        name    : the name of the object/file that was stored previously
    """

    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)


def print_obj(name):
    """
    Prints an object that was previously saved with the
    save_obj() function to stdout.
    
    Params:
        name    : the name of the object/file that was stored previously
    """

    from term_gui import make_header
    colors = ["blue", "red", "yellow", "magenta",  "cyan", "white"]*300
    obj = load_obj(name)
    
    it = 0
    for k, v in obj.items():
        try:
            coin = v["pair"]
        except:
            try:
                coin = v["asset"]
            except:
                try:
                    coin = v["altname"]
                except:
                    coin = "NameError"

        print(
            colored(
                make_header(
                    60,
                    str(coin),
                    boxed=True,
                    character="-",
                    centered=True
                ),
                colors[it]
            )
        )

        print(
            "ID: " + colored(str(k), "red")
        )

        try:
            for _, i in v.items():
                try:
                    if float(i) == 0:
                        i = int(float(i))
                    if float(i) < .1 and i != 0:
                        i = "{:.10f}".format(i)
                except: pass
                print(
                    _ + ": " + colored(str(i), "green")
                )
        except:
            print(str(v))

        it += 1


#
# ────────────────────────────────────────────────────── CREATING ORDER DICT ─────
#


def init_orders(verbose=False, log_file="order"):

    ret = {}
    history = orders_by_type("buy")

    for key, order in history.items():
        ret[key] = order
        floors = stop_limit(
            order["pair"],
            float(order["cost"]),
            float(order["vol"]),
            stop=.06,
            fee=(.0026009 * 2.0),
            limit=False,
            hard_floor=False # Use Default
        )
        ret[key].update(floors)
        ret[key].update(
            {
                "ceiling hit" : False,
                "floor hit" : False
            }
        )
        if verbose:
            print(
                order["pair"],
                floors,
                "\n"
            )
 
    save_obj(ret, log_file)


def orders_by_type(order_type):
    """
    Returns dictionary of trade history (up to 50 previous orders)
    that are either buys or sells only. If want all (buys and
    sells), just use trade_history() method.

    Params:
        order_type : "buy" or "sell"
    """

    ret = {}
    history = trade_history()
    for key, order in history.items():
        if order["type"] == order_type:
            ret[key] = order
    return ret


def display_status():
        
    from term_gui import make_header

    accounts = load_obj("order")

    usd_per_btc = get_price("XXBTZUSD")
    usd_per_eth = get_price("XETHZUSD")

    for identifier, order in accounts.items():

        curr_price = get_price(order["pair"])

        # ─────────────────────────────────────────────────────────────────

        distance_ceiling = ( float(order["ceiling"]) - float(curr_price) ) / float(curr_price)
        distance_floor = ( float(curr_price) - float(order["floor"]) ) / float(order["floor"])

        # ─────────────────────────────────────────────────────────────────

        # [ (1 refc / asset) * (volume asset / 1) * (1 usd / refc) ] = profit/loss value in USD

        difference = curr_price - float(order["price"])

        if order["pair"][-2:] == "BT":
            profit = ( ( difference ) * ( float(order["vol"]) ) * ( usd_per_btc ) )
        elif order["pair"][-3:] == "ETH":
            profit = ( ( difference ) * ( float(order["vol"]) ) * ( usd_per_eth ) )

        # ─────────────────────────────────────────────────────────────────

        print(
            colored(
                make_header(
                    60,
                    order["pair"],
                    tiers=2
                ),
                "cyan"
            )
        )

        # PROFIT/LOSS
        if profit > 0:
            print(
                colored(
                    ("[+] Profit: $" + str( f'{profit:.2f}')),
                    "green"
                )
            )
        else:
            print(
                colored(
                    ("[-] Loss: $" + str( f'{abs(profit):.2f}')),
                    "red"
                )
            )

        # PRICES
        print(
            "Purchase Price: ",
            colored(
                order["price"],
                "white"
            ),
            "\nCurrent Price: ",
            colored(
                f'{curr_price:.10f}',
                "white"
            ),
        )

        # CEILING
        print(
            colored(
                "\n─────────Ceiling────",
                "white"
            ),
            "\nPrice: ",
            colored(
                str(f'{order["ceiling"]:.10f}'),
                "blue"
            )
        )
        if order["ceiling hit"]:
            print(
                colored(
                    "[+] CEILING LIMIT ACTIVE",
                    "blue"
                )
            )
        if distance_ceiling > 0:
            print(
                "Distance To: ",
                colored(
                    (str( f'{(distance_ceiling * 100.0):.2f}' ) + "%"),
                    "blue"
                )
            )
        else:
            print(
                colored(
                    "Above Ceiling",
                    "blue"
                )
            )

        # FLOOR
        print(
            colored(
                "\n───────────Floor────",
                "white"
            ),
            "\nPrice: ",
            colored(
                str(f'{order["floor"]:.10f}'),
                "yellow"
            ),
        )
        if order["floor hit"]:
            print(
                colored(
                    "[!] FLOOR LIMIT ACTIVE",
                    "yellow"
                )
            )
        if distance_floor > 0:
            print(
                "Distance To: ",
                colored(
                    (str( f'{(distance_floor * 100.0):.2f}' ) + "%"),
                    "yellow"
                )
            )
        else:
            print(
                colored(
                    "Below Floor",
                    "yellow"
                )
            )
        
        # ID
        print(
            "\nOrder ID: ",
            identifier
        )


#
# ──────────────────────────────────────────────────────────── ADDING ORDERS ─────
#


def format_volume(pair, volume, direction="buy"):
    """
    pair        : trading pair abbreviation
    volume      : amount in currency used for purchase.
                  if buying, volume should be in reference currency;
                  if selling, volume should be in asset currency. 
    direction   : "sell" or "buy" (default)
    """
    # price = 1 refc / 1 assetc
    # 
    # if buy, volume is in refc
    #   if base is coin1 (assetc), convert volume to assetc
    #       (volume in refc) / (price) =
    #       (volume in refc) * (1 assetc / 1 refc) =
    #       volume in assetc
    #   if base is coin2 (refc), don't convert
    #  
    # if sell, volume is in assetc
    #   if base is coin1 (assetc), don't convert
    #   if base is coin2 (refc), convert volume to refc
    #       (volume in assetc) * (price) = 
    #       (volume in assetc) * (1 refc / 1 assetc) =
    #       volume in refc

    pair_info = asset_pair(pair)
    base = pair_info["base"]
    price = get_price(pair)

    if direction == "buy":
        ret_volume = ( float(volume) / float(price) ) if pair[:3] in base.upper() else float(volume)
    else:
        ret_volume = ( float(volume) * float(price) ) if pair[-3:] in base.upper() else float(volume)
        
    return ret_volume



# EXAMPLE
def d():

    btc_balance = 0.0039708840


    volume = format_volume("TRXXBT", (btc_balance / 4.0))

    print(
        "volume: ",
        str(volume)
    )
    print()
    print(
        add_order(
            "TRXXBT",
            "buy",
            volume,
            order_type="market",
            just_test=True
        )
    )




# TODO: make this cashed_out array a object that is saved with pickle
cashed_out = [
    "TWLB5X-GGUBR-TBLTOA",
    "TQUVKG-K6EZJ-EHIAUL",
    "TAGGOQ-JJI2E-DCXZXZ",
    "TSNK6A-L5WDR-4V5I5D",
    "TXLRQZ-LKSRJ-DVGLK2"
]

# TODO: update accounts object using dict creation function -- `update` so that user-created properties arent deleted

# TODO: use log file that takes all the verbose and print() functions/statements/blocks and adds headers indicating current time and other info

def threec_live():

    accounts = load_obj("order")
    for _ in cashed_out:
        try:
            del accounts[_]
        except: pass

    for identifier, order in accounts.items():

        time.sleep(1)
        curr_price = get_price(order["pair"])

        #
        # ─────────────────────────────────────────────────── CEILING ─────
        #

        if not order["ceiling hit"]:

            if curr_price >= order["ceiling"]:
                print(order["pair"])
                print("Ceiling Hit")
                # 1. cancel all orders
                # 2. change 'ceiling hit' value to True (and save object with pickle)
                # 3. change 'floor hit' value to False (incase it's not already)
                # 4. place limit order
        else:

            # Hitting Post-Ceiling Floor
            if curr_price <= order["post ceiling"]:
                print(order["pair"])
                print("Post-Ceiling Floor Hit")
                # 1. add order ID to cashed_out (and save object with pickle)
                # 2. update relevant balances (and save object with pickle)
            
            # New Ceiling on Continuous Rise
            if curr_price >= ( order["ceiling"] * 1.025 ):
                print(order["pair"])
                print("New Ceiling")
                # 1. cancel all orders
                # 2. place new limit order
                # 3. update dictionary values (and save object with pickle)
        
        #
        # ───────────────────────────────────────────────────── FLOOR ─────
        #

        if not order["floor hit"]:

            # Dip Below Floor
            if curr_price <= order["floor"]:
                print(order["pair"])
                print("Floor Hit")
                # 1. cancel all orders
                # 2. change 'floor hit' value to True
                # 3. change 'ceiling hit' value to False (incase it's not already)
                # 4. place limit order
        else:

            # Hitting Post-Floor Ceiling
            if curr_price >= order["post floor"]:
                print(order["pair"])
                print("Post-Floor Ceiling Hit")
                # 1. add order ID to cashed_out
                # 2. update relevant balances
            
        #
        # ──────────────────────────────────────────────── HARD FLOOR ─────
        #

            # Hitting Hard Floor after First Floor already Hit
            if curr_price <= order["hard flor"]:
                print(order["pair"])
                print("Hard Floor Hit")
                # 1. cancel all orders
                # 2. place new market order
                # 3. add order ID to cashed_out


balances = {
    'ZUSD': '0.0000', 
    'XXBT': '0.0039708840', 
    'XXDG': '2138.88730000', 
    'XXLM': '0.00000000', 
    'XETH': '0.0000000000', 
    'XETC': '6.0659800000', 
    'ADA': '0.00000000', 
    'NANO': '11.0950580000', 
    'LINK': '2.9777680000', 
    'PAXG': '0.0000000800', 
    'TRX': '522.78859639', 
    'MANA': '15.1407400000'
}


if __name__ == "__main__":
    pass
    #threec_live()