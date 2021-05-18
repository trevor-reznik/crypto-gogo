

# TODO: log file updates with each functions -- relevant info only -- time-coded
# TODO: refrence dictionary { pair_abbreviation : property formatted COIN - COIN } for fig header display function


import kraken_public as krakpub
import kraken_authenticated as krakauth

from termcolor import colored
import time
from term_gui import make_header
import persistent_objects as persistent

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
        fee = ( krakauth.usr_fees(trading_pair) + .0000009 ) * 2.0
    
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

    curr_dict = persistent.load_obj(log_file)
    history = orders_by_type("buy")
    delete = persistent.load_obj("cashed_out")

    color = "magenta"
    for key, order in history.items():

        # If order is already cashed out, delete the order record and skip this iteration
        if key in delete:
            if key in curr_dict.keys():
                del curr_dict[key]
            continue
        
        # Update the GET responses from krakauth.trade_history API call to saved order-dictionary-pickle-obj
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
    persistent.save_obj(curr_dict, log_file)


def orders_by_type(order_type):
    """
    Returns dictionary of trade history (up to 50 previous orders)
    that are either buys or sells only. If want all (buys and
    sells), just use krakauth.trade_history() method.

    Params:
        order_type : "buy" or "sell"
    """

    ret = {}
    history = krakauth.trade_history()
    for key, order in history.items():
        if order["type"] == order_type:
            ret[key] = order
    return ret




#
# ──────────────────────────────────────────────────── THREE CONDITIONS LIVE ─────
#


def threec_live():

    accounts = persistent.load_obj("order")
    for _ in persistent.load_obj("cashed_out"):
        try:
            del accounts[_]
        except: pass
    temp_bin = []

    # TODO -- save accounts object to pickle file at end of instance

    for identifier, order in accounts.items():

        curr_price = krakpub.get_price(order["pair"])
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
                response = krakauth.add_order(
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
                response = krakauth.add_order(
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
                response = krakauth.add_order(
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
                response = krakauth.add_order(
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


    persistent.save_obj(accounts, "order")



if __name__ == "__main__":
    pass
    threec_live()