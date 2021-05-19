###
###                                                                           
###      88888888ba,   88                       88                         
###      88      `"8b  ""                       88                         
###      88        `8b                          88                         
###      88         88 88 ,adPPYba, 8b,dPPYba,  88 ,adPPYYba, 8b       d8  
###      88         88 88 I8[    "" 88P'    "8a 88 ""     `Y8 `8b     d8'  
###      88         8P 88  `"Y8ba,  88       d8 88 ,adPPPPP88  `8b   d8'   
###      88      .a8P  88 aa    ]8I 88b,   ,a8" 88 88,    ,88   `8b,d8'    
###      88888888Y"'   88 `"YbbdP"' 88`YbbdP"'  88 `"8bbdP"Y8     Y88'     
###                                 88                            d8'      
###                                 88                           d8'       
###                                                                  
###       ad88888ba                                                  
###      d8"     "8b ,d                 ,d                           
###      Y8,         88                 88                           
###      `Y8aaaaa, MM88MMM ,adPPYYba, MM88MMM 88       88 ,adPPYba,  
###        `"""""8b, 88    ""     `Y8   88    88       88 I8[    ""  
###              `8b 88    ,adPPPPP88   88    88       88  `"Y8ba,   
###      Y8a     a8P 88,   88,    ,88   88,   "8a,   ,a88 aa    ]8I  
###       "Y88888P"  "Y888 `"8bbdP"Y8   "Y888  `"YbbdP'Y8 `"YbbdP"'  
###                         
###
###                                         
###                         ───────────────────────────────────────────────────────
###                         | Print status, progress, and notifications to stdout |
###                         ───────────────────────────────────────────────────────
###
###
###



from time import localtime, strftime

from termcolor import colored
from term_gui import make_header
from pyfiglet import Figlet

import persistent_objects as persistent 
import kraken_public as krakpub
import format_order
from asset_references import get_asset_pairs


def get_log_file():
    day = strftime("%b-%d-%Y", localtime())
    log_file = open("logs/" + day, "a+")
    return log_file


def timestamp_write(file, data):
    """
    Write current time to a file then write data

    Args:
        file : (file object)
        data : (str) message to be written after the timestamp
    """

    curr_time = strftime("%I:%M:%S", localtime())
    for _ in ["\n\nTIME: " + curr_time, "\n", data, "\n\n\n"]:
        file.write(_)


def acc_statement(pair, floor, ceiling, price, volume, wsname):
    """
    [ (1 refc / asset) * (volume asset / 1) * (1 usd / refc) ] = 
    profit/loss value in USD

    Args:
        pair : (str) asset pair
        floor : (float) floor price
        ceiling : (float) ceiling price
        price : (float) original purchase price
        volume : (float) original volume of purchase
        wsname : (string) asset pair's wsname property

    Returns:
        (dict)
            current price       : (str) current price to 10 decimals
            distance to ceiling : (str) distance as percent of current to 2 decimals if below ceiling
            distance to floor   : (str) distance as percent of current to 2 decimals if above floor
            difference          : (float) 
            profit              : (str|bool) False if none else profit in USD to 2 decimals
            loss                : (str|bool) False if none else loss in USD to 2 decimals

    """

    # TODO better system for this
    usd_per_btc = krakpub.get_price("XXBTZUSD")
    usd_per_eth = krakpub.get_price("XETHZUSD")

    floor, ceiling, volume, price = \
        float(floor), float(ceiling), float(volume), float(price)

    curr_price = float(krakpub.get_price(pair))
    distance_ceiling = ( ceiling - curr_price ) / curr_price
    distance_floor = ( curr_price - floor ) / floor

    difference = curr_price - price

    if "XBT" in wsname:
        profit = ( difference * ( volume ) * usd_per_btc )
    elif "ETH" in wsname:
        profit = ( difference * ( volume ) * usd_per_eth )

    ret = {
        "current price" : f'{curr_price:.10f}',
        "difference" : difference,
    }
    ret["profit"] = f'{profit:.2f}' if profit > 0 else False
    ret["loss"] = f'{abs(profit):.2f}' if profit <= 0 else False
    ret["distance to ceiling"] = "Above Ceiling" if distance_ceiling <= 0 else \
        f'{(distance_ceiling * 100.0):.2f}' + "%"
    ret["distance to floor"] = "Below Floor" if distance_floor <= 0 else \
        f'{(distance_floor * 100.0):.2f}' + "%"

    return ret


def profit_status(profit, loss, log_file):
    """
    """

    print("──────────────────{:^9}────────────────────".format("Position"))
    if profit:
        msg = "[+] Profit: $" + profit
        print(colored(msg, "green"))
    else:
        msg = "[-] Loss: $" + loss
        print(colored(msg, "red"))
    print()

    log_file.write("\n──────────────────{:^9}────────────────────\n".format("Position"))
    log_file.write(msg + "\n\n")


def price_status(original_price, currrent_price, log_file, color="white"):
    """
    Print and log original vs. current price to 10 decimals.
    """

    template = "| Purchase Price:                {}\n| Current Price:                 {}"
    try:
        original_price = f'{float(original_price):.10f}'
    except: pass

    print(
        template.format(
            colored(
                original_price,
                color
            ),
            colored(
                currrent_price,
                color

            )
        )
    )

    log_file.write(
        template.format(
            original_price, currrent_price
        )
    )
    

def threshold_status(log_file, threshold, name, hit, distance, color="green"):
    """
    Print and log status of order against given thresholds.
    
    Args:
        log_file  : (file object)
        threshold : (float|str) price threshold
        name      : (str) type of threshold
        hit       : (bool) if the threshold has been hit before
        distance  : (str) distance to threshold or msg indicating it's been hit
        color     : (str) (optional)
    """

    threshold = f'{threshold:.10f}' 
    template = "\n──────────────────{:^9}────────────────────\n{}| Price                         {}\n| Distance To                   {:>14}\n"
 
            
    print(
        template.format(
            name,
            colored("[!] " + name.upper() + " LIMIT ACTIVE\n" if hit else "", color),
            colored(threshold, "white"),
            colored(distance, color)
        )
    )
    log_file.write(
        template.format(
            name,
            "\n[!] " + name.upper() + " LIMIT ACTIVE [!]\n" if hit else "",
            threshold,
            distance
        )
    )


def extra_order_info(order, log_file):
    """
    """
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
    msgs = [
        "Initial Purchase Time: ",
        str(order["time"]),
        "\nInitial Cost: ",
        str(order["cost"]),
        "\nInitial Fee: ",
        str(order["fee"]),
        "\nInitial Volume: ",
        str(order["vol"]) + "\n\n"
    ]
    for _ in msgs: log_file.write(_)


def status(abridged=True):
    """
    Print and log status of active orders.

    Args:
        abridged        : (bool) True (default) = print only the important details
    """

    accounts = persistent.load_obj("orders_v1")
    pairs_dict = get_asset_pairs()
    log_file = get_log_file()

    for order in accounts.values():

        # header
        msg = make_header(
            60,
            order["pair"],
            tiers=2
        )
        print(colored(msg, "cyan"))
        timestamp_write(log_file, msg)

        # account statement/status
        statement = acc_statement(
            order["pair"],
            order["floor"],
            order["ceiling"],
            order["price"],
            order["vol"],
            pairs_dict[order["pair"]]["wsname"]
        )

        # profit/loss
        profit_status(
            statement["profit"],
            statement["loss"],
            log_file
        )

        # prices
        price_status(
            order["price"],
            statement["current price"],
            log_file
        )

        # thresholds
        threshold_status(
            log_file,
            order["ceiling"],
            "Ceiling",
            order["ceiling hit"],
            statement["distance to ceiling"],
            color = "green"
        )
        threshold_status(
            log_file,
            order["floor"],
            "Floor",
            order["floor hit"],
            statement["distance to floor"],
            color = "red"
        )

        # full unabridged info
        if not abridged: extra_order_info(order, log_file)


def single_order_status(id):
    """
    """

    pairs_dict = get_asset_pairs()
    log_file = get_log_file()
    order = persistent.load_obj("orders_v1")[id]

    # header
    msg = make_header(
        60,
        "Threshold Hit",
        tiers=2
    )
    timestamp_write(log_file, msg)

    # id
    print(
        "\nID: ",
        colored(
            id,
            "white"
        )
    )

    # account statement/status
    statement = acc_statement(
        order["pair"],
        order["floor"],
        order["ceiling"],
        order["price"],
        order["vol"],
        pairs_dict[order["pair"]]["wsname"]
    )

    # profit/loss
    profit_status(
        statement["profit"],
        statement["loss"],
        log_file
    )

    # prices
    price_status(
        order["price"],
        statement["current price"],
        log_file
    )

    # thresholds
    threshold_status(
        log_file,
        order["ceiling"],
        "Ceiling",
        order["ceiling hit"],
        statement["distance to ceiling"],
        color = "green"
    )
    threshold_status(
        log_file,
        order["floor"],
        "Floor",
        order["floor hit"],
        statement["distance to floor"],
        color = "red"
    )


def fig_alert(pair, valence, font=False, color=False, boxed=False):
    """
    Params:
        text        : string content of header
        valence     : "good", "bad", "neutral"
        border_header : boxed header above fig font. If not False, pass the text.
        font        : Figlet font. Leave blank for default based on valence.
        color       : Termcolor color. Leave blank for default based on valence.
        boxed       : Surrounded by '[+]' if True (default is False).
        termcolor   : if True (default), print in color. Else print normal.
    """


    # Defaults
    if not font:
        font = "starwars" if valence == "good" else "roman" if valence == "neutral" else "fender"
    if not color:
        color = "green" if valence == "good" else "blue" if valence =="neutral" else "red"
    if boxed:
        leader = "[+]" if valence == "good" else "[~]" if valence =="neutral" else "[-]"
    else: leader = ""
    
    f = Figlet(font=font) if len(pair) < 12 else Figlet(font="small",justify="center")

    from asset_references import get_asset_pairs
    wsname = get_asset_pairs()[pair]["wsname"].split("/") 
    text = " - ".join(wsname)

    text = f.renderText( leader + text + leader if len(text) < 8 else text )

    print( colored(text, color) )


def notify_order_place(order, direction, curr_price, server_response, color, ceiling=True):
    """
    Log and print when a new limit order is placed.
    """

    post = order["post ceiling"] if ceiling else order["post floor"]

    # logging
    log_file = get_log_file()
    timestamp_write(
        log_file,
        "[+] Limit Sell Order Placed with: " + \
            str(format_order.format_volume(order["pair"], order["vol"], direction=direction)) + \
                "of Base Currency"
    )
    msgs = [
        "at Price: ",
        str( format_order.format_price(post) ),
        "\n(" + str( f'{( ((curr_price - post) / curr_price ) * 100.0 ):.2f}' ) + "%" + " Below Current Price of",
        str( format_order.format_price(curr_price) ) + ")",
        "\nResponse from Server: ",
        str(server_response)
    ]
    for _ in msgs: log_file.write(_)

    # printing
    print(
        "\n\n[+] Limit Sell Order Placed with: ",
        colored(
            str(format_order.format_volume(order["pair"], order["vol"], direction=direction)),
            color
        ),
        "of Base Currency",
        "at Price: ",
        colored(
            str( format_order.format_price(post) ),
            color
        ),
        "\n(" + str( f'{( ((curr_price - post) / curr_price ) * 100.0 ):.2f}' ) +\
        "%" + " Below Current Price of",
        str( format_order.format_price(curr_price) ) + ")",
        colored(
            "\nIssuing Order Now . . . ",
            "grey"
        ),
        colored(
            "\n. . . Order Attempted . . .",
            "grey"
        ),
        "\nResponse from Server:\n",
        str(server_response)
    )

