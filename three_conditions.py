

# TODO: log file updates with each functions -- relevant info only -- time-coded


from tradebot import usr_fees, balance, trade_history, get_price, add_order, asset_pair
import pickle
from termcolor import colored
import time
from term_gui import make_header
from pyfiglet import Figlet
import sys

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
        hard_flooor     : the absolute floor that automatically triggers a market sell
        fee             : the scheduled fee percentage for this pair. default arg calls the API for each pair.
                          Alternatively, can use ( .20% + .26% ) as a standard.
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

    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    """
    Returns an object that was previously saved with the
    save_obj() function. 
    
    This Program's Stored Objects:
        order       : the dictionary of orders and floor/ceiling prices
        cashed_out  : the IDs of cashed out orders

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


def init_orders(log_file="order", new_thresholds=True, stop=.035, limit=False, hard_floor=False, fee=(.0026009 * 2.0), verbose=False):
    """
    Params:
        log_file        : the pickle obj file that contains the order dict that should be accessed
        new_thresholds  : if False, don't update dictionary with new floor calculations
        stop            : first floor/ceiling that activates the limit condition
        limit           : take-profit/stop-loss that's initiated after 1st condition is met
        hard_flooor     : the absolute floor that automatically triggers a market sell
        fee             : the scheduled fee percentage for this pair. "use API" arg calls the API for each pair.
                          Default value represents most common fee schedule.
    """

    curr_dict = load_obj(log_file)
    history = orders_by_type("buy")
    delete = load_obj("cashed_out")

    color = "magenta"
    for key, order in history.items():

        # If order is already cashed out, delete the order record and skip this iteration
        if key in delete:
            if key in curr_dict.keys():
                del curr_dict[key]
            continue
        
        # Update the GET responses from trade_history API call to saved order-dictionary-pickle-object
        else:
            try:
                curr_dict[key].update(order)
            except: curr_dict[key] = order
        # Call stop_limit to calculate floors/ceilings for each order unless new_thresholds is False
        try:
            if not new_thresholds:
                if order["ceiling"]:
                    pass
        # if new_thresholds is False but the order is brand new, create thresholds anyway
        except:
            floors = stop_limit(
                order["pair"],
                float(order["cost"]),
                float(order["vol"]),
                stop=stop,
                fee=fee,
                limit=limit,
                hard_floor=hard_floor
            )
            curr_dict[key].update(floors)

        # if new_thresholds is True
        if new_thresholds:
            floors = stop_limit(
                order["pair"],
                float(order["cost"]),
                float(order["vol"]),
                stop=stop,
                fee=fee,
                limit=limit,
                hard_floor=hard_floor
            )
            curr_dict[key].update(floors)

        # Check if 'ceiling hit' and 'floor hit' values already exist. If not, create
        try:
            if curr_dict[key]["ceiling hit"]:
                pass
            if curr_dict[key]["floor hit"]:
                pass
        except:
            curr_dict[key].update(
                {
                    "ceiling hit" : False,
                    "floor hit" : False
                }
            )


        if verbose:
            color = "green" if color == "magenta" else "cyan" if color == "green" else "magenta"
            print(
                colored(
                    make_header(
                        60,
                        order["pair"],
                        character="-",
                        centered=True,
                        boxed=True
                    ),
                    color
                ),
                colored(
                "\nThresholds from Chosen Algorithm:",
                "white"
                )
            )
            for _, x in floors.items():
                print(
                    _,
                    ":",
                    colored(
                        str(f'{x:.10f}'),
                        "blue"
                    )
                )
        if verbose:
            time.sleep(.8)

    time.sleep(.5)
    save_obj(curr_dict, log_file)


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


def cash_out(order_id):
    """
    pass the order ID's for orders whose initial purchase value
    was returned in base currency after cashing out. ID will be
    stored for persistent use.
    """
    current_list = load_obj("cashed_out")
    current_list.append(order_id)
    save_obj(current_list, "cashed_out")


def format_price(price, deciminals=6):
    return float(f'{(price):.6f}')


#
# ──────────────────────────────────────── STDOUT DISPLAYS AND NOTIFICATIONS ─────
#

# TODO: If log condition is True, save all print statements to a log file after formatting


def display_status(single_order=False, abridged=True, header=True):
    """
    Params:
        single_order    : If not False, pass an order ID to print only that order's Info.
                          If False, print all active buy-orders.
        abridged        : If False, prints extra info about order's initial purchase.
                          If True, print only the important details.
        header          : If False, don't print header for each order.
    """
        

    accounts = load_obj("order")
    cashed_out = load_obj("cashed_out")

    usd_per_btc = get_price("XXBTZUSD")
    usd_per_eth = get_price("XETHZUSD")

    for identifier, order in accounts.items():

        if single_order:
            if identifier != single_order:
                continue

        if identifier in cashed_out:
            continue

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

        if header:
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
        
        # EXTRA Info
        if not abridged:
            print(
                "Initial Purchase Time:",
                colored(
                    str(order["time"]),
                    "white"
                ),
                "\nInitial Cost:",
                colored(
                    str(order["cost"]),
                    "white"
                ),
                "\nInitial Fee:",
                colored(
                    str(order["fee"]),
                    "white"
                ),
                "\nInitial Volume:",
                colored(
                    str(order["vol"]),
                    "white"
                )
            )


def fig_alert(text, valence, border_header=False, font=False, color=False, boxed=False, termcolor=True, pair=True):
    """
    Params:
        text        : string content of header
        valence     : "good", "bad", "neutral"
        border_header : boxed heder above fig font. If not False, pass the text.
        font        : Figlet font. Leave blank for default based on valence.
        color       : Termcolor color. Leave blank for default based on valence.
        boxed       : Surrounded by '[+]' if True (default is False).
        termcolor   : if True (default), print in color. Else print normal.
        pair        : If True, text is a trading pair that should be split and hyphenated.
    """

    # Defaults
    if not font:
        font = "starwars" if valence == "good" else "roman" if valence == "neutral" else "fender"
    if not color:
        color = "green" if valence == "good" else "blue" if valence =="neutral" else "red"
    if boxed:
        leader = "[+]" if valence == "good" else "[~]" if valence =="neutral" else "[-]"
    else: leader = ""

    # Border Header
    if border_header:
        print(
            colored(
                make_header(
                    80,
                    border_header,
                    tiers=2
                ),
                color
            )
        )

    # Font
    text = str(text)
    f = Figlet(font=font) if len(text) < 12 else Figlet(font="small",justify="center")
    
    # Text
    if pair:
        text = text.replace("X","")
        if text[:3] in ["PAG", "LIN"]:
            if text[-2:] == "BT":
                text = text[:4] + " - " + text[-2:] + "C"
            else:
                text = text[:4] + " - " + text[-3:]
        else:
            text = text[:3] + " - " + text[-3:]
    text = f.renderText( leader + text + leader if len(text) < 8 else text )
    
    print( colored(text, color) ) if termcolor else text


def id_pair_display(identifier, pair, color="white"):
    print(
        "\nID: ",
        colored(
            identifier,
            "white"
        ),
        "PAIR: ",
        colored(
            pair,
            "white"
        )
    )


def notify_threshold_hit_change(from_ceiling, to_ceiling, from_floor, to_floor="False", color="white"):
    print(
        colored(
            "\n'Ceiling Hit'",
            color
        ),

        "Property Changed from",
        colored(
            str( from_ceiling ),
            color
        ),
        "to",
        colored(
            str( to_ceiling ),
            color
        ),

        colored(
            "\n'Floor Hit'",
            color
        ),
        "Property Changed from",
        colored(
            str( from_floor ),
            color
        ),
        "to",
        colored(
            str(to_floor),
            color
        )
    )


def notify_order_place(order, direction, curr_price, color, ceiling=True):

    post = order["post ceiling"] if ceiling else order["post floor"]

    print(
        "\n\n[+] Limit Sell Order Placed with: ",
        colored(
            str(format_volume(order["pair"], order["vol"], direction=direction)),
            color
        ),
        "of Base Currency",
        "at Price: ",
        colored(
            str( format_price(post) ),
            color
        ),
        "\n(" + str( f'{( ((curr_price - post) / curr_price ) * 100.0 ):.2f}' ) +\
        "%" + " Below Current Price of",
        str( format_price(curr_price) ) + ")",
        colored(
            "\nIssuing Order Now . . . ",
            "grey"
        ),
        colored(
            "\n. . . Order Attempted . . .",
            "grey"
        ),
        "\nResponse from Server:"
    )   


#
# ──────────────────────────────────────────────────── THREE CONDITIONS LIVE ─────
#


def threec_live():

    accounts = load_obj("order")
    for _ in load_obj("cashed_out"):
        try:
            del accounts[_]
        except: pass
    temp_bin = []

    # TODO -- save accounts object to pickle file at end of instance

    for identifier, order in accounts.items():

        curr_price = get_price(order["pair"])
        time.sleep(1.5)
        print("\n\n\n\n\n\n\n\n")

        # Temp Recylcye Bin -- ordres that have been cashed out but can't update accounts until iteration ends
        if identifier in temp_bin: continue

        #
        # ─────────────────────────────────────────────────── CEILING ─────
        #

        if not order["ceiling hit"]:


            # ─────────────────────────────────────────────────────────────────
            # ─── HITTING CEILING FOR FIRST TIME ──────────────────────────────

            if curr_price >= order["ceiling"]:

                # (1) Cancel All Orders
                # (2) Change 'ceiling hit'
                order["ceiling hit"] = True
                # (3) Change 'floor hit' value to False (incase it's not already)
                order["floor hit"] = False
                # (4) Place Limit Order
                response = add_order(
                    order["pair"],
                    "sell",
                    format_volume(order["pair"], order["vol"], direction="sell"),
                    price= format_price( order["post ceiling"] ),
                    order_type="limit",
                    just_test=True
                )
                # (5) Logging with Logfile and Notifying with Stdout
                fig_alert( order["pair"], "good", border_header="[+] CEILING HIT" )
                id_pair_display(identifier, order["pair"])
                display_status(single_order=identifier, header=False, abridged=True)
                notify_threshold_hit_change( order["ceiling hit"], "True",  order["floor hit"])
                notify_order_place(order, "sell", curr_price, "green", ceiling=True) 
                for k, v in response.items():
                    if not v: continue
                    print( colored( ( str(k) + "\n" + str(v) ), "blue") )


        else:


            # ─────────────────────────────────────────────────────────────────
            # ─── HITTING POST-CEILING FLOOR AFTER CEILING ────────────────────

            if curr_price <= order["post ceiling"]:
                # (1) Logging with Logfile and Notifying with Stdout
                fig_alert( order["pair"], "neutral", border_header="[~] POST-CEILING LIMIT HIT" )
                id_pair_display(identifier, order["pair"])
                display_status(single_order=identifier, header=False, abridged=True)
                # (2) File Away Order ID to cashed_out
                cash_out(identifier); temp_bin.append(identifier)
                # (3) Update Relevant Balances



            # ─────────────────────────────────────────────────────────────────
            # ─── NEW CEILING > MOON ──────────────────────────────────────────

            if curr_price >= ( order["ceiling"] * 1.04 ):
                # (1) Cancel All Orders
                # (2) Calculate New Thresholds + Update Dict Values
                order["post ceiling"] = order["ceiling"] * 1.035
                order["ceiling"] = order["ceiling"] * 1.04 #for calculations only
                # (3) Place New Limit Order with New Post Ceiling Limit
                response = add_order(
                    order["pair"],
                    "sell",
                    format_volume(order["pair"], order["vol"], direction="sell"),
                    price= format_price( order["post ceiling"] ),
                    order_type="limit",
                    just_test=True
                )
                # (4) Logging with Logfile and Notifying with Stdout
                fig_alert( order["pair"], "good", border_header="[+] NEW CEILING INITIATED" )
                id_pair_display(identifier, order["pair"])
                display_status(single_order=identifier, header=False, abridged=True)
                notify_order_place(order, "sell", curr_price, "green", ceiling=True) 
                print( "Previous Limit:", colored( (format_price ( order["post ceiling"] * .96618357487 )), "green"))
                print( "New Limit:", colored( (format_price ( order["post ceiling"] * .96618357487 )), "green" ))
                for k, v in response.items():
                    if not v: continue
                    print( colored( ( str(k) + "\n" + str(v) ), "blue") )
        
        #
        # ───────────────────────────────────────────────────── FLOOR ─────
        #

        if not order["floor hit"]:


            # ─────────────────────────────────────────────────────────────────
            # ─── DIP BELOW FLOOR ─────────────────────────────────────────────

            if curr_price <= order["floor"]:
                # (1) Cancel All Orders
                # (2) Change 'floor hit'
                order["floor hit"] = True
                # (3) Change 'ceiling hit' Value to False (incase it's not already)
                order["ceiling hit"] = False
                # (4) Place Limit Order
                response = add_order(
                    order["pair"],
                    "sell",
                    format_volume(order["pair"], order["vol"], direction="sell"),
                    price= format_price( order["post floor"] ),
                    order_type="limit",
                    just_test=True
                )
                # (5) Logging with Logfile and Notifying with Stdout
                fig_alert( order["pair"], "bad", border_header="[-] FLOOR HIT" )
                id_pair_display(identifier, order["pair"])
                display_status(single_order=identifier, header=False, abridged=True)
                notify_threshold_hit_change( order["floor hit"], "True",  order["ceiling hit"])
                notify_order_place(order, "sell", curr_price, "red", ceiling=False) 
                for k, v in response.items():
                    if not v: continue
                    print( colored( ( str(k) + "\n" + str(v) ), "blue") )

       
        else:


            # ─────────────────────────────────────────────────────────────────
            # ─── HITTING POST-FLOOR CEILING ──────────────────────────────────

            if curr_price >= order["post floor"]:
                # (1) Logging with Logfile and Notifying with Stdout
                fig_alert( order["pair"], "neutral", border_header="[~] POST-FLOOR LIMIT HIT" )
                id_pair_display(identifier, order["pair"])
                display_status(single_order=identifier, header=False, abridged=True)
                # (2) File Away Order ID to cashed_out
                cash_out(identifier); temp_bin.append(identifier)
                # (3) Update Relevant Balances


        #
        # ──────────────────────────────────────────────── HARD FLOOR ─────
        #


            # ─────────────────────────────────────────────────────────────────
            # ─── HITTING HARD FLOOR AFTER FIRST FLOOR ALREADY HIT ────────────

            if curr_price <= order["hard floor"]:
                # (1) Logging with Logfile and Notifying with Stdout
                fig_alert( order["pair"], "bad", border_header="[~] HARD FLOOR HIT" )
                id_pair_display(identifier, order["pair"])
                display_status(single_order=identifier, header=False, abridged=True)
                # (2) Cancel All Orders
                # (3) Place New Market Order
                response = add_order(
                    order["pair"],
                    "sell",
                    format_volume(order["pair"], order["vol"], direction="sell"),
                    price= format_price( order["hard floor"] ),
                    order_type="market",
                    just_test=True
                )
                # (4) File Away Order ID to cashed_out
                cash_out(identifier); temp_bin.append(identifier)
                # (5) Logging with Logfile and Notifying with Stdout
                notify_order_place(order, "sell", curr_price, "red", ceiling=True) 
                for k, v in response.items():
                    if not v: continue
                    print( colored( ( str(k) + "\n" + str(v) ), "blue") )


    save_obj(accounts, "order")



if __name__ == "__main__":
    pass
    if len(sys.argv) > 1:
        if sys.argv[1] == "--update-orders":
            init_orders(verbose=True)
        elif sys.argv[1] == "--status":
            display_status()
    else:
        threec_live()
