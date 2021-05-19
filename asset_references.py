###   
###   
###         .o.                                       .   
###        .888.                                    .o8   
###       .8"888.      .oooo.o  .oooo.o  .ooooo.  .o888oo 
###      .8' `888.    d88(  "8 d88(  "8 d88' `88b   888   
###     .88ooo8888.   `"Y88b.  `"Y88b.  888ooo888   888   
###    .8'     `888.  o.  )88b o.  )88b 888    .o   888 . 
###   o88o     o8888o 8""888P' 8""888P' `Y8bod8P'   "888" 
###                                                       
###                                                       
###                                                       
###   ooooooooo.              .o88o.                                                              
###   `888   `Y88.            888 `"                                                              
###    888   .d88'  .ooooo.  o888oo   .ooooo.  oooo d8b  .ooooo.  ooo. .oo.    .ooooo.   .ooooo.  
###    888ooo88P'  d88' `88b  888    d88' `88b `888""8P d88' `88b `888P"Y88b  d88' `"Y8 d88' `88b 
###    888`88b.    888ooo888  888    888ooo888  888     888ooo888  888   888  888       888ooo888 
###    888  `88b.  888    .o  888    888    .o  888     888    .o  888   888  888   .o8 888    .o 
###   o888o  o888o `Y8bod8P' o888o   `Y8bod8P' d888b    `Y8bod8P' o888o o888o `Y8bod8P' `Y8bod8P' 
###                                                                                               
###                                                                                               
###                                                                                               
###   oooooooooo.    o8o                .            
###   `888'   `Y8b   `"'              .o8            
###    888      888 oooo   .ooooo.  .o888oo  .oooo.o 
###    888      888 `888  d88' `"Y8   888   d88(  "8 
###    888      888  888  888         888   `"Y88b.  
###    888     d88'  888  888   .o8   888 . o.  )88b 
###   o888bood8P'   o888o `Y8bod8P'   "888" 8""888P' 
###                                                  
###                                                  
###   
###   



from kraken_public import all_asset_pairs
import persistent_objects as persistent
from time import time, localtime


def scheduled_update(data, days_between_updates=14):
    """ Check last time a persistent-object data structure was updated from
        an API call (in order to determine whether or not to refresh the data
        or keep using data on file).
        Returns False if interval between now and last update is greater than
        days_between_updates arg; else, True.

        Params:
            data : (str) [asset_pair, ]
            days_between_updates : (int) max days before data should be updated (default 14)
    """

    saved_obj_names = {
        "asset_pair" : "day_of_last_asset_update"
    }

    ref_data = saved_obj_names[data]

    curr_yrday = localtime(time())[7]
    last_yrday = persistent.load_obj(ref_data)["day of year"]

    overwrite_obj = {
        "day of year" : curr_yrday,
        "interval" : days_between_updates
        }
    persistent.save_obj(overwrite_obj, ref_data)

    # New Calendar Year (yrdays are in range [0,365])
    if curr_yrday < last_yrday: curr_yrday += 365

    if curr_yrday - last_yrday >= days_between_updates:
        return True
    return False


def get_asset_pairs(days_between_updates=21):
    """ Returns dictionary of asset-pairs information. If time between
        now and last udpate is greater than days_between_updates, refresh
        dictionary with API call, otherwise return saved dictionary.

        Params:
            days_between_updates: (int) max days before data should be updated (default 21)
    """

    if scheduled_update("asset_pair", days_between_updates):
        return all_asset_pairs()
    else:
        return persistent.load_obj("asset_reference_dict")
