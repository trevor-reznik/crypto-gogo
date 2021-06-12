###   
###   
###   ooooooooooooo oooo                                          .oooooo.   
###   8'   888   `8 `888                                         d8P'  `Y8b  
###        888       888 .oo.   oooo d8b  .ooooo.   .ooooo.     888          
###        888       888P"Y88b  `888""8P d88' `88b d88' `88b    888          
###        888       888   888   888     888ooo888 888ooo888    888          
###        888       888   888   888     888    .o 888    .o    `88b    ooo  
###       o888o     o888o o888o d888b    `Y8bod8P' `Y8bod8P'     `Y8bood8P'  
###                                                                          
###                                                                          



from term_gui import make_header
import display_status
import kraken_public as krakpub
import kraken_authenticated as krakauth
import persistent_objects as persistent
import format_order
from crud_orders import crud
import time


def threec_thresholds(trading_pair, refc_cost, asset_balance, stop=False, limit=False, hard_floor=False, fee="use API"):
    """
    Get price for all three conditions in a dictionary.
    If only want floor/ceiling price with given percent, then only use
    the associated values in the returned dict.
    Leave optional params as False in order to use default percentages.

    Args:
        trading_pair    : Kraken abbreviation for the trading pair
        refc_cost       : cost of initial trade in the reference currency
        asset_balance   : volume of trade in the asset (owned/purchased) currency
        stop            : first floor/ceiling that activates the limit condition
        limit           : take-profit/stop-loss that's initiated after 1st condition is met
        hard_flooor     : the absolute floor that automatically triggers a market sell
        fee             : the scheduled fee percentage for this pair. default arg calls the API for each pair.
                          Alternatively, can use ( .20% + .26% ) as a standard.
    Returns:
        (dict)
            ceiling_price,
            post_ceiling_price,
            floor_price,
            post_floor_price,
            hard_floor_price
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


def update_thresholds(orders_obj, stop=.035, limit=False, hard_floor=False, fee=(.0026009 * 2.0)):
    """
    Update orders object with three conditions type thresholds

    Args:
        stop        : first floor/ceiling that activates the limit condition
        limit       : take-profit/stop-loss that's initiated after 1st condition is met
        hard_flooor : the absolute floor that automatically triggers a market sell
        fee         : the scheduled fee percentage for this pair. "use API" arg calls the API for each pair.
                      Default value represents most common fee schedule.
    """

    for id, order in orders_obj.items():
        if "post ceiling" not in order.keys():
            floors = threec_thresholds(
                order["pair"],
                float(order["cost"]),
                float(order["vol"]),
                stop=stop,
                fee=fee,
                limit=limit,
                hard_floor=hard_floor
            )
            orders_obj[id].update(floors)
            orders_obj[id]["ceiling hit"] = False
            orders_obj[id]["floor hit"] = False


def print_log_header(header):
    """
    """

    header = make_header(
        60,
        header,
        tiers=2
    )

    # log header
    display_status.timestamp_write(
        display_status.get_log_file(),
        header
    )

    # print header
    print(header)


def above_ceiling(order, id, curr_price):
    """
    (1) Cancel All Orders
    (2) Change 'ceiling hit'
    (3) Change 'floor hit' value to False (incase it's not already)
    (4) Place Limit Order
    """

    order["ceiling hit"] = True
    order["floor hit"] = False
    response = krakauth.add_order(
        order["pair"],
        "sell",
        format_order.format_volume(order["pair"], order["vol"], direction="sell"),
        price= format_order.format_price( order["post ceiling"] ),
        order_type="limit",
        just_test=True
    )

    print_log_header("[+] ceiling hit for first time")
    display_status.fig_alert(order["pair"], "good")
    display_status.single_order_status(id)
    display_status.notify_order_place(order, "sell", curr_price, response, "green", ceiling=True) 


def beneath_floor(order, id, curr_price):
    """
    (1) Cancel All Orders
    (2) Change 'floor hit'
    (3) Change 'ceiling hit' Value to False (incase it's not already)
    (4) Place Limit Order
    (5) Logging with Logfile and Notifying with Stdout
    """

    order["floor hit"] = True
    order["ceiling hit"] = False
    response = krakauth.add_order(
        order["pair"],
        "sell",
        format_order.format_volume(order["pair"], order["vol"], direction="sell"),
        price= format_order.format_price( order["post floor"] ),
        order_type="limit",
        just_test=True
    )

    print_log_header("[-] floor hit for first time")
    display_status.fig_alert( order["pair"], "bad")
    display_status.single_order_status(id)
    display_status.notify_order_place(order, "sell", curr_price, response, "red", ceiling=False) 


def post_ceiling_floor(order, id):
    """
    (1) Logging with Logfile and Notifying with Stdout
    (2) File Away Order ID to cashed_out
    """

    print_log_header("[~] POST-CEILING LIMIT HIT")
    display_status.fig_alert( order["pair"], "good")
    display_status.single_order_status(id)
    crud.cash_out(id)


def post_floor_ceiling(order, id):
    """
    (1) Logging with Logfile and Notifying with Stdout
    (2) File Away Order ID to cashed_out
    """

    print_log_header("[~] post-floor ceiling hit")
    display_status.fig_alert( order["pair"], "neutral")
    display_status.single_order_status(id)
    crud.cash_out(id)


def raise_ceiling(order, id, curr_price, percent_increase):
    """
    (1) Cancel All Orders
    (2) Calculate New Thresholds + Update Dict Values
    (3) Place New Limit Order with New Post Ceiling Limit
    (4) Logging with Logfile and Notifying with Stdout
    """

    msgs = ["Previous Limit: " + str(format_order.format_price(order["post ceiling"]))]

    order["post ceiling"] = order["ceiling"] * ( percent_increase - .05 )
    order["ceiling"] = order["ceiling"] * percent_increase #for calculations only

    response = krakauth.add_order(
        order["pair"],
        "sell",
        format_order.format_volume(order["pair"], order["vol"], direction="sell"),
        price= format_order.format_price( order["post ceiling"] ),
        order_type="limit",
        just_test=True
    )

    print_log_header("[^] new ceiling initiated")
    display_status.fig_alert(order["pair"], "good")
    display_status.single_order_status(id)
    display_status.notify_order_place(order, "sell", curr_price, response, "green", ceiling=True) 

    msgs.append("New Limit: " + str(format_order.format_price(order["post ceiling"])))
    for _ in msgs: print_log_header(_)
    

def hard_floor(order, id, curr_price):
    """
    (1) Logging with Logfile and Notifying with Stdout
    (2) Cancel All Orders
    (3) Place New Market Order
    (4) File Away Order ID to cashed_out
    (5) Logging with Logfile and Notifying with Stdout
    """

    response = krakauth.add_order(
        order["pair"],
        "sell",
        format_order.format_volume(order["pair"], order["vol"], direction="sell"),
        price= format_order.format_price( order["hard floor"] ),
        order_type="market",
        just_test=True
    )
    crud.cash_out(id)
    
    print_log_header("[!] hard floor hit")
    print_log_header("[!] market order placed")
    display_status.fig_alert( order["pair"], "bad")
    display_status.single_order_status(id)
    display_status.notify_order_place(order, "sell", curr_price, response, "red", ceiling=False) 


def threec_live(orders_name="orders_v1", trash_name="cashed_out_v1"):

    try:
        while True:

            # refresh orders object
            crud(orders_obj=orders_name)
            accounts = persistent.load_obj(orders_name)
            orders_unchanged = True

            while orders_unchanged:
                for id, order in accounts.items():

                    curr_price = krakpub.get_price(order["pair"])
                    #time.sleep(3)

                    if not order["ceiling hit"]:
                        if curr_price >= order["ceiling"]:
                            # !!! don't initiate limit order below current price
                            if curr_price < order["ceiling"] * 1.03:
                                above_ceiling(order, id, curr_price)
                            else:
                                raise_ceiling(order, id, curr_price, 1.03)
                                orders_unchanged = False
                    else:
                        if curr_price <= order["post ceiling"]:
                            post_ceiling_floor(order, id)
                            orders_unchanged = False
                        elif curr_price >= ( order["ceiling"] * 1.01 ):
                            raise_ceiling(order, id, curr_price, 1.03)
                            orders_unchanged = False

                    if not order["floor hit"]:
                        if curr_price <= order["floor"]:
                            beneath_floor(order, id, curr_price)
                    else:
                        if curr_price >= order["post floor"]:
                            post_floor_ceiling(order, id)
                            orders_unchanged = False
                        elif curr_price <= order["hard floor"]:
                            hard_floor(order, id, curr_price)
                            orders_unchanged = False
            
            # save accounts object whenever breaking
            persistent.save_obj(accounts, orders_name)
            time.sleep(1)

    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    threec_live()