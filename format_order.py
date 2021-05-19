###   
###   
###   oooooooooooo                                                    .   
###   `888'     `8                                                  .o8   
###    888          .ooooo.  oooo d8b ooo. .oo.  .oo.    .oooo.   .o888oo 
###    888oooo8    d88' `88b `888""8P `888P"Y88bP"Y88b  `P  )88b    888   
###    888    "    888   888  888      888   888   888   .oP"888    888   
###    888         888   888  888      888   888   888  d8(  888    888 . 
###   o888o        `Y8bod8P' d888b    o888o o888o o888o `Y888""8o   "888" 
###                                                                       
###                                                                       
###                                                                       
###     .oooooo.                  .o8                     
###    d8P'  `Y8b                "888                     
###   888      888 oooo d8b  .oooo888   .ooooo.  oooo d8b 
###   888      888 `888""8P d88' `888  d88' `88b `888""8P 
###   888      888  888     888   888  888ooo888  888     
###   `88b    d88'  888     888   888  888    .o  888     
###    `Y8bood8P'  d888b    `Y8bod88P" `Y8bod8P' d888b    
###                                                                                                
###
### 
###               ───────────────────────────────────────────────────
###               |                                                 |
###               |   Helper function to format orders correctly    |
###               |                                                 | 
###               ───────────────────────────────────────────────────
###
###



import kraken_public as krakpub


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

    pair_info = krakpub.asset_pair(pair)
    base = pair_info["base"]
    price = krakpub.get_price(pair)

    if direction == "buy":
        ret_volume = ( float(volume) / float(price) ) if pair[:3] in base.upper() else float(volume)
    else:
        ret_volume = ( float(volume) * float(price) ) if pair[-3:] in base.upper() else float(volume)
        
    return ret_volume


def format_price(price, deciminals=6):
    return float(f'{(price):.6f}')