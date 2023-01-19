""" Didactic example of TkFire being used

In this version, a simple GUI demonstrating input and output on a static GUI

This demonstrates:
  - How to make and reference Memory and TkFire objects
  - How to bind a command post build but before running

@author: Ben C
"""


from tkfire import *
import tkinter as tk


# Define some convenience constants
BOTH33 = {'fill': 'both', 'ipadx': 3, 'ipady': 3}
TB33 = {'side': 'top', 'fill': 'both', 'ipadx': 3, 'ipady': 3}
LB33 = {'side': 'left', 'fill': 'both', 'ipadx': 3, 'ipady': 3}


# #### Step 1 ####
# Create variables or other functions which will plug into the GUI
options = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
memory = Memory(btn_cmd=lambda *_: print("Hello!"),
                opt_A=tk.IntVar,
                opt_B=tk.IntVar,
                opt_C=tk.IntVar)


# #### Step 2 ####
# Define the structure of the GUI
# There will be left panel with two buttons stacked vertically
# There will be right panel with three option-menus stacked vertically
mother = {
    'left_panel': {
        LAYOUT: fire_pack(**LB33),
        TYPE: spec(tk.LabelFrame, text="Left Side", width=24),
        CHILDREN: {
            # The first button will print "Hello!" to the console
            'hello_button': {
                # Bind the "btn_cmd" function to the button
                TYPE: spec(tk.Button, text="Say Hello", width=12, command=memory["btn_cmd"]),
                LAYOUT: fire_grid(),
            },
            'calc_button': {
                # We can bind later as well, so omit 'command=...' for now
                TYPE: spec(tk.Button, text="A + B + C", width=12),
                LAYOUT: fire_grid(),
            }
        }
    },
    'right_panel': {
        'LAYOUT': fire_pack(**LB33),
        'TYPE': spec(tk.LabelFrame, text="Right Side", width=24),
        'CHILDREN': {
            # Create the three drop-down menus, each will provide the values present in options as allowable options
            "option_A": {
                # OptionMenu widgets must be bound to a tkinter variable, here we reference the IntVar variables
                # stored in memory, and we will give then default/initial values with the 'value=#' kwarg
                TYPE: spec(tk.OptionMenu, Memory.varspec(f'opt_A'), *options),
                LAYOUT: fire_pack(**TB33)
            },
            "option_B": {
                TYPE: spec(tk.OptionMenu, Memory.varspec(f'opt_B', value=2), *options),
                LAYOUT: fire_pack(**TB33)
            },
            "option_C": {
                TYPE: spec(tk.OptionMenu, Memory.varspec(f'opt_C', value=4), *options),
                LAYOUT: fire_pack(**TB33)
            },
        },
    },
}


# #### Step 3 ####
# create a Tk or TopLevel object for the GUI
tk_core = tk.Tk()
# Create the TkFire object
my_gui = TkFire(tk_core, memory, mother).build()

# Let us add a command to the 'calc_button' in the 'left_panel'
# Note: memory['opt_A'] -> tk.IntVar
#       to retrieve the value stored in a tkinter Variable, the get() method must be called
my_gui.bind_command(
    'left_panel!calc_button',
    lambda *_: print(memory[f'opt_A'].get() + memory[f'opt_B'].get() + memory[f'opt_C'].get())
)

# Run the gui
tk_core.mainloop()
