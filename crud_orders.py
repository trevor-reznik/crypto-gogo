def cash_out(order_id):
    """
    pass the order ID's for orders whose initial purchase value
    was returned in base currency after cashing out. ID will be
    stored for persistent use.
    """
    current_list = persistent.load_obj("cashed_out")
    current_list.append(order_id)
    persistent.save_obj(current_list, "cashed_out")
