""" Didactic example of TkFire being used


TODO: Update the examples

@author: Ben C
"""


from tkfire import *
import tkinter as tk
from tkinter import scrolledtext as st


from pprint import pprint
import yaml
from io import StringIO


BOTH33 = {'fill': 'both', 'ipadx': 3, 'ipady': 3}
TB33 = {'side': 'top', 'fill': 'both', 'ipadx': 3, 'ipady': 3}
LB33 = {'side': 'left', 'fill': 'both', 'ipadx': 3, 'ipady': 3}


def print_hello():
    print("Hello")


# #### Step 1 ####
# create a Tk or TopLevel object for the GUI
tk_core = tk.Tk()


# #### Step 2 ####
# Create variables or other functions which will plug into the GUI
n_options = 3
memory = Memory(options=[1,2,3,4,5],
                btn_cmd=lambda: print("Hello!"))
for i in range(0, n_options):
    memory[f'Opt{i+1}'] = tk.IntVar



# #### Step 2b ####
# create any custom widgets you may need
class YamlBox:
    def __init__(self, core):
        self.core = core
        self.frame = tk.Frame(self.core)
        self.container = tk.Frame(self.frame)
        self.container.pack(**TB33)
        self.scrolly = tk.Scrollbar(self.container)
        self.scrollx = tk.Scrollbar(self.container, orient='horizontal')
        self.scrolly.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollx.pack(side=tk.BOTTOM, fill=tk.X)
        self.textbox = tk.Text(self.container,
                               yscrollcommand=self.scrolly.set,
                               xscrollcommand=self.scrollx.set,
                               width=18,
                               height=5,
                               wrap=tk.NONE)
        self.textbox.pack(**LB33)
        self.scrolly.config(command=self.textbox.yview)
        self.scrollx.config(command=self.textbox.xview)
        self.notif_frame = tk.Frame(self.frame)
        self.notif_frame.pack(**TB33)
        self.notification = tk.Label(self.notif_frame, text='--')
        self.notification.pack(**BOTH33)

    def get(self, start, end):
        text = self.textbox.get(start, end)
        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError as ye:
            mark = ye.problem_mark  # noqa: a YAMLError does contain the problem_mark attribute, PyCharm helper
            # is having some issues with this line
            line = mark.line + 1
            column = mark.column + 1
            self.notification['text'] = f'YAML Error: L{line} C{column}'
            return None
        else:
            self.notification['text'] = '--'
            return doc

    def delete(self, start, end):
        return self.textbox.delete(start, end)

    def insert(self, where, what):
        stream = StringIO()
        yaml.safe_dump(what, stream)
        self.textbox.insert(where, stream.getvalue())
        del stream

    def pack(self, *args, **kwargs):
        return self.frame.pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        return self.frame.grid(*args, **kwargs)

    def call_on_master(self, key, *args, **kwargs):
        return getattr(self.frame, key)(*args, **kwargs)


# #### Step 3 ####
# Define the structure of the GUI
# 'Name of Element' (cannot contain '!')
#      LAYOUT: [packing method ('pack' or 'grid'), args]
#      TYPE: [name of tk, st, ttk, or custom widget, args]
#      CHILDREN: (Optional) dict(Elements for which this element is the parent frame)
mother = {
    'left_panel': {
        LAYOUT: fire_pack(expand=True, **LB33),
        TYPE: spec(tk.LabelFrame, text="Left Side", width=16),
        CHILDREN: {
            'Button1': {
                TYPE: spec(tk.Button, text="Button 1"),
                LAYOUT: fire_grid(row=0, column=0),
            },
            'Button2': {
                TYPE: spec(tk.Button, text="Button 2!", command="btn_cmd"),
                LAYOUT: fire_grid(row=1, column=0),
            },
            'Button3': {
                TYPE: spec(tk.Button, text="Button 3", command=print_hello),
                LAYOUT: fire_grid(row=2, column=0),
            },
            'my_yaml_box': {
                TYPE: spec(YamlBox),
                LAYOUT: fire_grid(row=0, column=1, rowspan=3),
                POST: [spec('insert', where="1.0", what=[1, 2, 3, 5, 8, 13]), ]
            },
            'scrolled_text': {
                TYPE: spec(st.ScrolledText, wrap=tk.WORD, width=16, height=12),
                LAYOUT: fire_grid(row=3, column=1),
                CHILDREN: {
                    'my_entry': {
                        TYPE: spec(tk.Entry),
                        LAYOUT: fire_pack(**LB33)
                    }
                }
            }
        },
        POST: [
            spec('rowconfigure', 1, weight=1),
            spec('rowconfigure', 2, weight=1),
        ]
    },
    'right_panel': {
        'LAYOUT': fire_pack(**LB33),
        'TYPE': spec(tk.LabelFrame, text="Right Side", width=16),
        'CHILDREN': {
            **{  # Variable elements can be defined with comprehensions
                f"Option{i}": {
                    TYPE: spec(tk.OptionMenu, memory.varspec(f'Opt{i}'), 0, memory.varg('options', 1)),
                    LAYOUT: fire_pack(**TB33),
                } for i in range(1, n_options)
            },
            f"Option{n_options}": {
                    TYPE: spec(tk.OptionMenu, memory.varspec(f'Opt{n_options}'), 0, *[-1, -2, -3, -4]),
                    LAYOUT: fire_pack(**TB33),
            }
            # The first set of Option Menus used 'options' (a reference to memory) to specify values
            # The final Option Menu uses
        },
    },
}


# #### Step 4 ####
# Create the TkFire object (if no generator is provided, it will use the default version)
my_gui = TkFire(tk_core, memory, mother).build()

# In order to address GUI elements after creation, use a bang-path get/set item:
my_gui['left_panel!scrolled_text!my_entry'].insert(0, "hello world")
my_gui['left_panel!Button1']['text'] = "Get Yaml Input"


# #### Step 4b ####
# Examples of editing the GUI before execution

# A button's functionality can be bound after creation
def update_test(t, v):
    t[0] = v


test = [None, ]
my_gui.bind_command(
    'left_panel!Button1',
     lambda *_: update_test(test, my_gui.gui['left_panel!my_yaml_box'].get("1.0", tk.END))
)

# OptionMenu widgets can be updated
my_gui.set_optionmenu_options('right_panel!Option1', [2, 4, 6, 8])

# The GUI can be modified using tkinter grammar after creation as well
my_gui['left_panel!Button4'] = tk.Button(my_gui['left_panel'],
                                         text="Button 4?",
                                         command=lambda *_: print(
                                             sum(memory[f'Opt{j}'].get() for j in range(1, n_options + 1))
                                         )
                                         )
my_gui['left_panel!Button4'].grid(row=3, column=0)


# #### Step 5 ####
# Run the gui
tk_core.mainloop()


# #### Post ####

# print("\nGUI")
# pprint(my_gui.gui)

print("Memory")
pprint(my_gui.memory)

print("\nTest")
pprint(test[0])
