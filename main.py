import tkfire
from tkfire import tk, LAYOUT, TYPE, CHILDREN, LB33, TB33, BOTH33, PACK_SCROLL

from pprint import pprint
import yaml
from io import StringIO


# Step 1, create a Tk or TopLevel object for the GUI
core = tk.Tk()

# Step 2, Create variables or other functions which will plug into the GUI
memory = dict()
memory['Opt1'] = tk.IntVar
memory['Opt2'] = tk.IntVar
memory['Opt3'] = tk.IntVar
memory['options'] = [1, 2, 3, 4, 5]
memory['btn_cmd'] = lambda: print("Hello")


# Step 2b, create any custom widgets you may need
class YamlBox:
    def __init__(self, core):
        self.core = core
        self.frame = tk.Frame(self.core)
        # self.frame.pack(**TB33)
        self.container = tk.Frame(self.frame)
        self.container.pack(**TB33)
        self.scrolly = tk.Scrollbar(self.container)
        self.scrollx = tk.Scrollbar(self.container, orient='horizontal')
        self.scrolly.pack(PACK_SCROLL)
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
            mark = ye.problem_mark  # it's fine
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


# Step 2c, Create a generatrix for the TkFire object
generator = tkfire.Generatrix({'YAML_Entry': YamlBox})

# Step 3, Define the structure of the GUI
# 'Name of Element' (cannot contain '!')
#      LAYOUT: [packing method ('pack' or 'grid'), args]
#      TYPE: [name of tk, st, ttk, or custom widget, args]
#      CHILDREN: (Optional) dict(Elements for which this element is the parent frame)
mother = {
    'left_panel': {
        LAYOUT: ['pack', LB33],
        TYPE: ["LabelFrame", {'text': "Left Side", 'width': 16}],
        CHILDREN: {
            'Button1': {
                TYPE: ['Button', {'text': "Button 1", 'command': 'btn_cmd'}],
                LAYOUT: ['grid', {'row': 0, 'column': 0}],
            },
            'Button2': {
                TYPE: ['Button', {'text': "Button 2", 'command': 'btn_cmd'}],
                LAYOUT: ['grid', {'row': 1, 'column': 0}],
            },
            'Button3': {
                TYPE: ['Button', {'text': "Button 3", 'command': 'btn_cmd'}],
                LAYOUT: ['grid', {'row': 2, 'column': 0}],
            },
            'my_yaml_box': {
                TYPE: ['YAML_Entry', {}],
                LAYOUT: ['grid', {'row': 0, 'column': 1, 'rowspan': 3}]
            },
            'scrolled_text': {
                TYPE: ["ScrolledText", {'wrap': tk.WORD, 'width': 16, 'height': 12}],
                LAYOUT: ['grid', {'row': 3, 'column': 1}],
                CHILDREN: {
                    'my_entry': {
                        TYPE: ['Entry', {}],
                        LAYOUT: ['pack', LB33]
                    }
                }
            }
        },
    },
    'right_panel': {
        'LAYOUT': ['pack', LB33],
        'TYPE': ["LabelFrame", {'text': "Right Side", 'width': 16}],
        'CHILDREN': {
            'Option1': {
                TYPE: ['OptionMenu', {'variable': ['Opt1', {'value': 0}], 'values': 'options'}],
                LAYOUT: ['pack', TB33],
            },
            'Option2': {
                TYPE: ['OptionMenu', {'variable': ['Opt2', {'value': 0}], 'values': 'options'}],
                LAYOUT: ['pack', TB33],
            },
            'Option3': {
                TYPE: ['OptionMenu', {'variable': ['Opt3', {'value': 0}], 'values': 'options'}],
                LAYOUT: ['pack', TB33],
            },
        },
    },
}

# Step 4, Create the TkFire object (if no generator is provided, it will use the default version)
my_gui = tkfire.TkFire(core, memory, mother, generator=generator)

# In order to address GUI elements after creation, use a bang-path call on the 'gui' attribute:
my_gui.gui['left_panel!scrolled_text!my_entry'].insert(0, "hello world")

# Step 5, Run the gui
core.mainloop()

pprint(my_gui.gui)
