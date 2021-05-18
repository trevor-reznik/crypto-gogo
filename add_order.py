###   
###   
###         .o.             .o8        .o8       .oooooo.                  .o8                     
###        .888.           "888       "888      d8P'  `Y8b                "888                     
###       .8"888.      .oooo888   .oooo888     888      888 oooo d8b  .oooo888   .ooooo.  oooo d8b 
###      .8' `888.    d88' `888  d88' `888     888      888 `888""8P d88' `888  d88' `88b `888""8P 
###     .88ooo8888.   888   888  888   888     888      888  888     888   888  888ooo888  888     
###    .8'     `888.  888   888  888   888     `88b    d88'  888     888   888  888    .o  888     
###   o88o     o8888o `Y8bod88P" `Y8bod88P"     `Y8bood8P'  d888b    `Y8bod88P" `Y8bod8P' d888b    
###                                                                                               
###
### 
###                                     ──────────────────────────────────────────────────
###                                     |                                                |
###                                     |   Issue order via Kraken authenticated API     |
###                                     |                                                | 
###                                     ──────────────────────────────────────────────────
###
###



import kraken_public as krakpub
import kraken_authenticated as krakauth
import persistent_objects as persistent

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