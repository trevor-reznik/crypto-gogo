
# Maker and Taker Fee Schedules:
# https://support.kraken.com/hc/en-us/articles/360000526126-What-are-Maker-and-Taker-fees-


from tradebot import usr_fees, balance


# ────────────────────────────────────────────────────────────────────────────────
# ─── CONDITION A - STOP LOSS LIMIT ──────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────────


def ceiling(coin, refcoin, buy_in_nominal, balance_in_refc, stop_profit=.03, limit_profit=False):
    """
    Returns:
    (1) Rise Ceiling
    (2) Post-Ceiling-Applied Limit Floor

    Params:
    buy_in_nominal  : the nominal amount of owned currency bought in 
                      initial trade
    balance_in_refc : the balance of the currnecy in the reference 
                      currency
    stop_profit     : the first limit that activates the new stop
                      loss floor (as a percentage profit)
    limit_profit    : the stop loss floor that is initiated after
                      the first condition is met (as a percentage of
                      profit less than the stop_profit percentage)
    """
    fee = ( usr_fees(coin, refcoin) + .0000009 ) * 2.0

    if not limit_profit:
        limit_profit = stop_profit / 2.0

    ceiling_percent = 1.0 + fee + stop_profit
    limit_percent = 1.0 + fee + limit_profit

    ceiling_price = ( buy_in_nominal * ceiling_percent ) / float(balance_in_refc)
    limit_price = ( buy_in_nominal * limit_percent ) / float(balance_in_refc)

    return [ceiling_price, limit_price]


# ────────────────────────────────────────────────────────────────────────────────
# ─── CONDITION B AND C - TAKE PROFIT LIMIT AND HARD STOP LOSS FLOOR ─────────────
# ────────────────────────────────────────────────────────────────────────────────

def floor(coin, refcoin, buy_in_nominal, balance_in_refc, stop_loss=.03, limit_profit=False, hard_floor=False):
    """
    Returns:
    (1) Dip Floor
    (2) Post-Floor-Applied Limit Ceiling
    (3) Hard Floor Price

    Params:
    buy_in_nominal  : the nominal amount of owned currency bought in 
                      initial trade
    balance_in_refc : the balance of the currnecy in the reference 
                      currency
    stop_loss       : the first limit that activates the new take
                      profit ceiling (as a negative percentage loss)
    limit_profit    : the take profit ceiling that is initiated after
                      the first condition is met (as a negative 
                      percentage of loss)
    """

    if not hard_floor:
        hard_floor = stop_loss * 1.75

    if not limit_profit:
        limit_profit = stop_loss / 2.0

    hard_floor_percent = 1.0 - hard_floor
    floor_percent = 1.0 - stop_loss
    limit_percent = 1.0 - limit_profit
    
    hard_floor_price = ( buy_in_nominal * hard_floor_percent ) / float(balance_in_refc)
    floor_price = ( buy_in_nominal * floor_percent ) / float(balance_in_refc)
    limit_price = ( buy_in_nominal * limit_percent ) / float(balance_in_refc)

    return [floor_price, limit_price, hard_floor_price]


# ────────────────────────────────────────────────────────────────────────────────


