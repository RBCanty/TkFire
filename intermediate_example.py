""" Didactic example of TkFire being used

In this version, a GUI demonstrating input and output on a dynamic GUI
(The options present in the GUI will depend on input from the user)

This demonstrates:
  - Using comprehensions to rapidly expand a GUI
  - Creating and using a custom Widget (although the example does not subclass the tkinter Widget base class)
  - The addition of Widgets after build but before execution
  - The specification of Memory elements to be unpacked later, to a specified depth (none, *, vs **)
  - Modifying a TkFire GUI instance using traditional tkinter grammar
  - Using stubs
  - Updating Widget properties during runtime (admittedly, using a quality-of-life method built-in to TkFire)
  - Using the POST specification to perform actions on Widgets after creation but during build

@author: Ben C
"""

from tkfire import *
import tkinter as tk
from tkinter import scrolledtext as st
from pprint import pprint
import yaml
from io import StringIO

# Define some convenience constants
BOTH33 = {'fill': 'both', 'ipadx': 3, 'ipady': 3}
TB33 = {'side': 'top', 'fill': 'both', 'ipadx': 3, 'ipady': 3}
LB33 = {'side': 'left', 'fill': 'both', 'ipadx': 3, 'ipady': 3}
n_options = 4


def print_hello():
    print("Hello")


# #### Step 1 ####
# Create variables or other functions which will plug into the GUI
# Memory can be initialized from a dictionary
memory = {
    'options': [1, 2, 3, 4, 5],
    'btn_cmd': print_hello,
    **{
        f'opt{i}': tk.IntVar for i in range(n_options)
    }
}
memory = Memory(memory)


# The same expression using kwarg syntax:
# memory = Memory(options=[1, 2, 3, 4, 5],
#                 btn_cmd=print_hello,
#                 **{
#                     f'opt{i}': tk.IntVar for i in range(n_options)
#                 })


# create any custom widgets you may need


class YamlBox:
    def __init__(self, core):
        self.core = core
        self.frame = tk.Frame(core)
        self.textbox = st.ScrolledText(self.frame, width=24, height=6, wrap=tk.NONE)
        self.textbox.vbar2 = tk.Scrollbar(self.frame, orient='horizontal')
        self.textbox['xscrollcommand'] = self.textbox.vbar2.set
        self.textbox.vbar2.config(command=self.textbox.xview)
        self.notification = tk.Label(self.frame, text='--')
        # Packing
        self.textbox.pack(expand=True, **TB33)
        self.textbox.vbar2.pack(side=tk.TOP, fill=tk.X)
        self.notification.pack(**TB33)

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


# #### Step 2 ####
# Define the structure of the GUI
# There will be a left panel with 3 buttons stacked vertically and a scrollable box that
#   treats its text as YAML-encoded to the right
# There will be a right panel with n_options OptionMenu option-menus stacked vertically
mother = {
    'left_panel': {
        LAYOUT: fire_pack(expand=True, **LB33),
        TYPE: spec(tk.LabelFrame, text="Left Side", width=24),
        CHILDREN: {
            'hello_button': {
                # Since memory has the key 'btn_cmd' we can write "command='btn_cmd'" and the interpreter
                #   will look it up for us.
                TYPE: spec(tk.Button, text="Hello 1", command='btn_cmd'),
                LAYOUT: fire_grid(row=0, column=0),
            },
            'set_range_button': {
                TYPE: spec(tk.Button),  # Fill in later
                LAYOUT: fire_grid(row=1, column=0),
            },
            # If we want to make something after build, we can either leave a comment
            # along the lines of "to do later: add a button" or we can specify a 'stub'
            # in the mother dictionary.  We can store layout information here such that
            # it is all kept in one place.
            'sum_button': {
                TYPE: stub(),
                LAYOUT: fire_grid()
            },
            'my_yaml_box': {
                TYPE: spec(YamlBox),
                LAYOUT: fire_grid(row=0, column=1, rowspan=4, sticky="NSEW"),
                # POST executes after creation and packing of this widget
                # This will call:
                #   self.insert(where="1.0", what=...)
                # where self is the YamlBox created for this Widget, my_yaml_box
                # Here the 'options' value needs to not be unpacked (we want it as a list)
                # In this example, we could have equivalently said "what=memory['options']"
                POST: [post('insert', where="1.0", what=memory.varg('options', 0)), ]
            },
        },
        # POST: for making the buttons shift when the window is resized
        # This will call:
        #   self.columnconfigure(0, weight=1)
        #   self.rowconfigure((0,1,2), weight=1)
        # where self is the LabelFrame created for this Widget, left_panel
        POST: [
            post('columnconfigure', (0, 1), weight=1),
            post('rowconfigure', (0, 1, 2), weight=1),
        ]
    },
    'right_panel': {
        'LAYOUT': fire_pack(**LB33),
        'TYPE': spec(tk.LabelFrame, text="Right Side", width=24),
        'CHILDREN': {
            # Variable/repeated elements can be defined with comprehensions
            **{
                f"menu_{i}": {
                    # Should a variable referenced in memory require unpacking, we can specify so
                    # In this example, we could have equivalently said "*memory['options']"
                    TYPE: spec(tk.OptionMenu, memory.varspec(f'opt{i}'), memory.varg('options', 1)),
                    LAYOUT: fire_pack(**TB33),
                } for i in range(n_options)
            }
        },
    },
}

# #### Step 3 ####
# create a Tk or TopLevel object for the GUI
tk_core = tk.Tk()
# Create the TkFire object (if no generator is provided, it will use the default version)
my_gui = TkFire(tk_core, memory, mother).build()

# First, let us add the missing details for the set_range_button Button
# We can still access properties using tkinter syntax (i.e., widget[option] = ...)
my_gui['left_panel!set_range_button']['text'] = "Update menus"


# Make a function that will update memory and the OptionMenu widgets such that the list of
#   options is the list present in the YamlBox widget...
def update_menus(a_gui: TkFire):
    yaml_output = a_gui.gui['left_panel!my_yaml_box'].get("1.0", tk.END)
    a_gui.memory['options'] = yaml_output
    for i in range(n_options):
        a_gui.set_optionmenu_options(f'right_panel!menu_{i}', yaml_output)


# ...then bind it to the set_range_button button
my_gui.bind_command(
    'left_panel!set_range_button',
    lambda *_: update_menus(my_gui)
)

# Second, let us add that 'sum_button'
# The GUI can be modified using traditional tkinter grammar
my_gui.build_stub('left_panel!sum_button',
                  tk.Button,
                  text="Sum Menus",
                  command=lambda *_: print(
                      sum(memory[f'opt{j}'].get() for j in range(n_options))  # noqa: See note at bottom
                  )
                  )

# # If we did not make a 'stub' in the mother, we could also have added this widget
# #   after build using traditional tkinter grammar
# my_gui['left_panel!sum_button'] = tk.Button(
#     my_gui['left_panel'],
#     text="Sum Menus",
#     command=lambda *_: print(
#         sum(memory[f'opt{j}'].get() for j in range(n_options))  # noqa: See note at bottom
#     )
# )
# my_gui['left_panel!sum_button'].grid()

# Run the gui
tk_core.mainloop()

print("Memory")
pprint(my_gui.memory)

# Some IDEs may generate a warning because memory was assigned as:
# memory[f'opt{j}'] -> tk.IntVar
# Which is a type and does not have a get() method
# But after building:
# memory[f'opt{j}'] -> tk.IntVar(...)
# Which is the class and does have a get() method
