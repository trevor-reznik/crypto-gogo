#
# ───────────────────────────────────────────────── USING PERSISTENT OBJECTS ─────
#
import pickle
from termcolor import colored
from term_gui import make_header


def save_obj(obj, name):
    """
    Saves an object to a file for persistent use between
    program instances. 
    
    Params:
        obj     : the object to save
        name    : the name of the file to write to/create
    """

    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    """
    Returns an object that was previously saved with the
    save_obj() function. 
    
    This Program's Stored Objects:
        order       : the dictionary of orders and floor/ceiling prices
        cashed_out  : the IDs of cashed out orders

    Params:
        name    : the name of the object/file that was stored previously
    """

    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)


def print_obj(name):
    """
    Prints an object that was previously saved with the
    save_obj() function to stdout.
    
    Params:
        name    : the name of the object/file that was stored previously
    """

    colors = ["blue", "red", "yellow", "magenta",  "cyan", "white"]*300
    obj = load_obj(name)
    
    it = 0
    for k, v in obj.items():
        try:
            coin = v["pair"]
        except:
            try:
                coin = v["asset"]
            except:
                try:
                    coin = v["altname"]
                except:
                    coin = "NameError"

        print(
            colored(
                make_header(
                    60,
                    str(coin),
                    boxed=True,
                    character="-",
                    centered=True
                ),
                colors[it]
            )
        )

        print(
            "ID: " + colored(str(k), "red")
        )

        try:
            for _, i in v.items():
                try:
                    if float(i) == 0:
                        i = int(float(i))
                    if float(i) < .1 and i != 0:
                        i = "{:.10f}".format(i)
                except: pass
                print(
                    _ + ": " + colored(str(i), "green")
                )
        except:
            print(str(v))

        it += 1