try:
    from termcolor import colored, cprint
except:
    import os
    os.system("pip3 install termcolor")
    from termcolor import colored, cprint


class term_gui:
    def __init__(self, every=True, strong=True, temperatures=True, emphasis=True, highlight=True, attributes=True):
        self.gui = {}

        if every:
            self.gui["all color"] = ["grey", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
        if temperatures:
            self.gui["cool color"] = ["blue", "green", "magenta",  "cyan", "white"]
            self.gui["warm color"] = ["red", "yellow"]
        if emphasis:
            self.gui["bright color"] = ["red", "green", "yellow", "blue"]
            self.gui["hidden color"] = ["grey"]
        if highlight:
            self.gui["highlight"] = ["on_grey", "on_red", "on_green", "on_yellow", "on_blue",
                        "on_magenta", "on_cyan", "on_white"]
        if attributes:
            self.gui["attr"] = {"bold":"bold","dark":"dark","underline":"underline",\
                    "blinking":"blink","reversed":"reverse","concealed":"concealed"}
        if strong:
            self.gui["strong color"] = ["red", "yellow"]

        self.complement = {
            "red" : "green",
            "green" : "magenta",
            "grey" : "white",
            "white" : "grey",
            "yellow" : "blue",
            "blue" : "yellow",
            "magenta" : "green",
            "cyan" : "red",
        }
        self.headers = [
            { "fill" : 75,
            "template" : "\n\n\n" + "{0}"*80 + "\n{0}{0}{0} {1} {2}\n" + "{0}"*80
            },
            { "fill" : 55,
            "template" : "\n\n\n" + "{0}"*60 + "\n{0}{0}{0} {1} {2}\n" + "{0}"*60
            },
            { "fill" : 35,
            "template" : "\n\n\n" + "{0}"*40 + "\n{0}{0}{0} {1} {2}\n" + "{0}"*40
            },
            { "fill" : 25,
            "template" : "\n\n\n" + "{0}"*30 + "\n{0}{0}{0} {1} {2}\n" + "{0}"*30
            },
            { "fill" : 25,
            "template" : "\n\n\n" + "{0}"*30 + "\n{0}{0}{0} {1} {2}\n"
            },
            { "fill" : 45,
            "template" : "\n{0}{0}{0} {1} {2}\n"
            },
            { "fill" : 25,
            "template" : "\n{0}{0}{0} {1} {2}\n"
            },
            { "fill" : 0,
            "template" : "\n{0}{0}{0}{0}{0}{0} {1} {0}{0}{0}{0}{0}{0}{2}\n"
            },
            { "fill" : 0,
            "template" : "\n{0}{0}{0} {1} {0}{0}{0}{2}\n"
            },
        ]

        self.info = "termcolor module methods:\n\
            ------------------------\n\
            cprint(str, color, highlight-color)\n\
            print(colored(str, color, attrs=[attributes]))\n\n\
            term_gui class methods:\n\
            ------------------------\n\
            get_gui(all=True, strong=True, temperatures=True, emphasis=True\
            highlight=True, attributes=True)\n"


def make_header(gui_length, text, character="─", centered=False, tiers=3, boxed=False, auto_capitalize=True, style="triple bar", middle_leader=3):
    gui_length = int(gui_length)
    middle_leader = int(middle_leader)
    tiers = int(tiers)
    if auto_capitalize:
        text = str(text).upper()
    else:
        text = str(text)
    character = str(character)[0]
    ret = ""

    if style == "triple bar" or style:

        # Top Tier
        if tiers > 1:
            ret+= "\n\n " + character * gui_length + "\n"
            if tiers > 3:
                for _ in range( (tiers - 3) // 2 ):
                    ret+= " " + character * gui_length + "\n"
        else:
            ret += "\n\n"

        # Middle Tier
        if boxed:
            mid_char = " "
        else:
            mid_char = character
        ret = ret + " |" if boxed else ret + " "

        if not centered:
            ret += mid_char * int(middle_leader) + \
                " " + str(text).strip() + " " + \
                    mid_char * ( (gui_length - (2 + int(middle_leader))) - len(text) )
        if centered:
            if boxed:
                fill = ( gui_length - ( len(text) + 4 ) ) // 2
            if not boxed:
                 fill = ( gui_length - ( len(text) + 2 ) ) // 2
            ret += ( mid_char * fill ) + " " + str(text).strip() + " " + ( mid_char * fill )
            if ( gui_length - (len(text) + 2) ) % 2:
                ret += mid_char 
        
        ret = ret[:-2] + "|\n" if boxed and not centered else ret + "|\n" if boxed and centered else ret + "\n"

        # Bottom Tier
        if tiers > 2:
            ret += " " + character * gui_length + "\n"
            if tiers > 3:
                for _ in range( ((tiers - 3) // 2) + (tiers - 3) % 2 ):
                    ret+= " " + character * gui_length + "\n"
            ret += "\n"
        else:
            ret += "\n\n"
    
    return ret