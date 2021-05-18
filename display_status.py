###                                                                           
###         88888888ba,   88                       88                         
###         88      `"8b  ""                       88                         
###         88        `8b                          88                         
###         88         88 88 ,adPPYba, 8b,dPPYba,  88 ,adPPYYba, 8b       d8  
###         88         88 88 I8[    "" 88P'    "8a 88 ""     `Y8 `8b     d8'  
###         88         8P 88  `"Y8ba,  88       d8 88 ,adPPPPP88  `8b   d8'   
###         88      .a8P  88 aa    ]8I 88b,   ,a8" 88 88,    ,88   `8b,d8'    
###         88888888Y"'   88 `"YbbdP"' 88`YbbdP"'  88 `"8bbdP"Y8     Y88'     
###                                    88                            d8'      
###                                    88                           d8'       
###                                                                     
###          ad88888ba                                                  
###         d8"     "8b ,d                 ,d                           
###         Y8,         88                 88                           
###         `Y8aaaaa, MM88MMM ,adPPYYba, MM88MMM 88       88 ,adPPYba,  
###           `"""""8b, 88    ""     `Y8   88    88       88 I8[    ""  
###                 `8b 88    ,adPPPPP88   88    88       88  `"Y8ba,   
###         Y8a     a8P 88,   88,    ,88   88,   "8a,   ,a88 aa    ]8I  
###          "Y88888P"  "Y888 `"8bbdP"Y8   "Y888  `"YbbdP'Y8 `"YbbdP"'  
###                            
###
###                                         
###                         -------------------------------------------------------
###                         | Print status, progress, and notifications to stdout |
###                         -------------------------------------------------------
###
###    TODO:
###    [+] If log condition is True, save all print statements to a log file after formatting
   


import persistent_objects as persistent 


def status(single_order=False, abridged=True, header=True):
    """
    Params:
        single_order    : If not False, pass an order ID to print only that order's Info.
                          If False, print all active buy-orders.
        abridged        : If False, prints extra info about order's initial purchase.
                          If True, print only the important details.
        header          : If False, don't print header for each order.
    """
        

    accounts = persistent.load_obj("order")
    cashed_out = persistent.load_obj("cashed_out")

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

