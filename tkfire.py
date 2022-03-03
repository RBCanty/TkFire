import tkinter as tk
from tkinter import scrolledtext as st
from tkinter import ttk


LAYOUT = 'LAYOUT'
TYPE = 'TYPE'
CHILDREN = 'CHILDREN'
PACK_SCROLL = {'side': 'right', 'fill': 'y'}
BOTH33 = {'fill': 'both', 'ipadx': 3, 'ipady': 3}
TB33 = {'side': 'top', 'fill': 'both', 'ipadx': 3, 'ipady': 3}
LB33 = {'side': 'left', 'fill': 'both', 'ipadx': 3, 'ipady': 3}


class Generatrix:
    def __init__(self, custom_elements=None):
        if custom_elements is None:
            custom_elements = dict()
        self.custom_elements = custom_elements

    def __getattr__(self, item):
        if item in dir(tk):
            return getattr(tk, item)
        elif item in dir(st):
            return getattr(st, item)
        elif item in dir(ttk):
            return getattr(ttk, item)
        elif item in self.custom_elements:
            return self.custom_elements[item]
        else:
            raise ModuleNotFoundError(item)


def grid_arg(row, col, kwargs=None):
    if kwargs is None:
        kwargs = {}
    args = {'row': row, 'column': col}
    args.update(kwargs)
    return args


class TkFire:
    def __init__(self, core, memory, mother, generator=Generatrix()):
        self.core = core
        self.memory = memory
        self.mother = mother
        self.generator = generator
        self.gui = dict()
        self.build("", self.mother)

    def build(self, parent, structure):
        if parent:
            root = self.gui[parent]
            path = parent + "!"
        else:
            root = self.core
            path = ""
        for k, child in structure.items():
            index = path + k
            kwargs = child[TYPE][1]
            args = list()
            has_scrolly = False
            has_scrollx = False
            if 'variable' in kwargs:
                self.memory[kwargs['variable'][0]] = self.memory[kwargs['variable'][0]](root, **kwargs['variable'][1])
                args.append(self.memory[kwargs['variable'][0]])
                del child[TYPE][1]['variable']
            if 'command' in kwargs:
                child[TYPE][1]['command'] = self.memory[kwargs['command']]
            if 'values' in kwargs:
                args += self.memory[kwargs['values']]
                del child[TYPE][1]['values']
            if 'scrolly' in kwargs:
                has_scrolly = True
                del child[TYPE][1]['scrolly']
            if 'scrollx' in kwargs:
                has_scrollx = True
                del child[TYPE][1]['scrollx']
            self.gui[index] = getattr(self.generator, child[TYPE][0])(root, *args, **child[TYPE][1])
            getattr(self.gui[index], child[LAYOUT][0])(**child[LAYOUT][1])
            if has_scrolly:
                self.gui[index + '!Scrolly'] = tk.Scrollbar(root)
                self.gui[index]['yscrollcommand'] = self.gui[index + '!Scrolly'].set
                self.gui[index + '!Scrolly'].config(command=self.gui[index].yview)
                self.gui[index + '!Scrolly'].pack(**PACK_SCROLL)
            if has_scrollx:
                self.gui[index + '!Scrollx'] = tk.Scrollbar(root)
                self.gui[index]['xscrollcommand'] = self.gui[index + '!Scrollx'].set
                self.gui[index + '!Scrollx'].config(command=self.gui[index].xview)
                self.gui[index + '!Scrollx'].pack(**{'side': tk.BOTTOM, 'fill': tk.X})
            if CHILDREN in child.keys():
                self.build(index, child[CHILDREN])

    def destroy(self):
        self.core.destroy()
