###   
###   
###     .oooooo.   ooooooooo.   ooooo     ooo oooooooooo.   
###    d8P'  `Y8b  `888   `Y88. `888'     `8' `888'   `Y8b  
###   888           888   .d88'  888       8   888      888 
###   888           888ooo88P'   888       8   888      888 
###   888           888`88b.     888       8   888      888 
###   `88b    ooo   888  `88b.   `88.    .8'   888     d88' 
###    `Y8bood8P'  o888o  o888o    `YbodP'    o888bood8P'   
###                                                         
###                                                         
###                                                         
###     .oooooo.                  .o8                              
###    d8P'  `Y8b                "888                              
###   888      888 oooo d8b  .oooo888   .ooooo.  oooo d8b  .oooo.o 
###   888      888 `888""8P d88' `888  d88' `88b `888""8P d88(  "8 
###   888      888  888     888   888  888ooo888  888     `"Y88b.  
###   `88b    d88'  888     888   888  888    .o  888     o.  )88b 
###    `Y8bood8P'  d888b    `Y8bod88P" `Y8bod8P' d888b    8""888P' 
###                                                                
###                                                                
###   



import persistent_objects as persistent
from kraken_authenticated import trade_history

from termcolor import colored
from term_gui import make_header


#
# ────────────────────────────────────────────────────────── UPDATING ORDERS ─────
#


def query_history(order_type):
    """
    Returns dictionary of trade history (up to 50 previous orders)
    that are either buys or sells only. If want all (buys and
    sells), just use krakauth.trade_history() method.

    Params:
        order_type : "buy" or "sell"
    """

    ret = {}
    history = trade_history()
    for key, order in history.items():
        if order["type"] == order_type:
            ret[key] = order
    return ret


def add_from_API(orders_obj, cashed_obj="cashed_out"):
    """
    """

    history = query_history("buy")
    cashed_out = persistent.load_obj(cashed_obj) # (list)

    for id in history.keys():
        # if not cashed out and not already in orders dictionary 
        if id not in cashed_out and id not in orders_obj.keys():
            orders_obj[id] = history[id]



#
# ────────────────────────────────────────────────────────── REMOVING ORDERS ─────
#


def cash_out(order_id):
    """
    pass the order ID's for orders whose initial purchase value
    was returned in base currency after cashing out. ID will be
    stored for persistent use.
    """

    current_list = persistent.load_obj("cashed_out")
    current_list.append(order_id)
    persistent.save_obj(current_list, "cashed_out")


def delete_cashed(order_obj, cashed_obj="cashed_out"):
    """
    Delete any orders in the order dict that are already cashed out.

    Args:
        order_obj   : (dict) the orders dictionary to update
        cashed_obj  : (str) the file name of the cashed out pickle object file
    """

    trash = persistent.load_obj(cashed_obj) # (list)

    for id in trash:
        if id in order_obj.keys():
            del order_obj[id]


#
# ──────────────────────────────────────────────────────────────────── MAIN ─────
#


def initialize_objects(subcategory=False):
    """
    Initialize and save order history and cashed out pickle objects 
    for new user or new, isolated trading strategy set.

    Args:
        subcategory : (bool) if True, this is a secondary set of dictionaries for a returning user
    """

    import os

    iterator = 1
    orders_name = "orders_v" + str(iterator) 
    trash_name = "cashed_out_v" + str(iterator)
    current_objects = os.listdir("obj/")

    while orders_name in current_objects or trash_name in current_objects:
        orders_name = "orders_v" + str(iterator) 
        trash_name = "cashed_out_v" + str(iterator)
        iterator += 1


    orders = query_history("buy")
    cashed_out = []

    if subcategory:
        for _ in orders.key(): cashed_out.append(_)
    persistent.save_obj(cashed_out, trash_name)

    if subcategory:
        delete_cashed(orders, cashed_obj=trash_name)
    persistent.save_obj(orders, orders_name)


def crud(orders_obj="orders_v1"):
    """
    Delete cashed out, add from API trade history, save objects.
    
    Args:
        orders_obj      : (str) pickle obj file name that contains the persistent order dict
    """

    try:
        orders = persistent.load_obj(orders_obj)
        delete_cashed(orders)
        add_from_API(orders)
    except Exception as e:
        print(e)
        if "y" in input("Error accessing user data.\nInitialize New Orders Dictionary? [Y/N]\n").lower():
            initialize_objects()

    persistent.save_obj(orders, orders_obj)