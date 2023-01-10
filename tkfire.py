""" A helper module to allow a tkinter GUI to be defined from a dictionary (collapsable in IDE) with the ability to
reference components by Name.

@author: Richard "Ben" Canty
"""

import tkinter as tk
from tkinter import scrolledtext as st
from tkinter import ttk
from pprint import pformat


__all__ = ["TkFire", "Dispatcher",
           "grid_arg",
           "LAYOUT", "TYPE", "CHILDREN"]


LAYOUT = 'LAYOUT'
TYPE = 'TYPE'
CHILDREN = 'CHILDREN'
PACK_SCROLL = {'side': 'right', 'fill': 'y'}


class Dispatcher:
    """ Defines the Method Resolution Order for TkFire: tk > st > ttk > custom """
    def __init__(self, custom_elements=None, mro=None):
        """ Creates a dispatcher which will be provided with keywords and then determine which
        module/object to call when constructing them.

        **Ordering**: tkinter.tk, tkinter.scrolledtext, tkinter.ttk, custom_elements
        --> raise ModuleNotFoundError

        References: :class:`TkFire`

        :param custom_elements: (Optional) a dict of user-made classes (keyed by class name as
          referenced in TkFire's mother)
        :param mro: (default: tk, st, ttk) An iterable of modules, in order of method resolution
        """
        if custom_elements is None:
            custom_elements = dict()
        if mro is None:
            mro = [tk, st, ttk, ]
        self._mro = mro
        self.custom_elements = custom_elements

    def generate(self, item, *args, **kwargs):
        """ Is given a constructor (or a key to dispatch to a constructor) and returns an instantiated version of
        the object.

        :param item: A constructor or a string mapped to a constructor
        :param args: positional arguments for the constructor
        :param kwargs: keyword arguments for the constructor
        :return: constructor(*args, **kwargs)
        """
        if not isinstance(item, str):
            return item(*args, **kwargs)
        return getattr(self, item)(*args, **kwargs)

    def __getattr__(self, item):
        for _module in self._mro:
            if item in dir(_module):
                return getattr(_module, item)
        if item in self.custom_elements:
            return self.custom_elements[item]
        else:
            raise ModuleNotFoundError(item)


def grid_arg(row, col, kwargs=None):
    """ Used to abridge the specification of the tkinter grid packer

    Reference:
      - columnspan: How many columns a widget occupies (default 1)
      - rowspan: How many rows a widget occupies (default 1)
      - ipadx, ipady: How many pixels to pad inside the widget's borders, horizontally and vertically
      - padx, pady: How many pixels to pad outside the widget's borders, horizontally and vertically
      - sticky: What to do if the cell is larger than widget
        (center - "", side/corner - combinations of "N", "S", "E", & "W")

    :param row: the row number (0-indexed)
    :param col: the column number (0-indexed)
    :param kwargs: And additional kwargs for grid (see note)
    :return: A dict of keyword arguments for grid()
    """
    if kwargs is None:
        kwargs = {}
    args = {'row': row, 'column': col}
    args.update(kwargs)
    return args


class TkFireStructuralError(Exception):
    pass


class TkFireSpecificationError(Exception):
    pass


class TkFire:
    """ A Wrapper for tkinter for a nicer experience in an IDE

    Elements of the GUI are of the form {name: {layout: [], type: [], children: {}}}

    - name will define how the element is references in the self.gui dictionary
    - layout keys to a list whose first element is the layout method (e.g. pack, grid) and whose
      second element is a dictionary of the kwargs which are passed to the layout method.
    - type keys to a list whose first element is the name of the Widget (e.g. LabelFrame, Button)
      and whose second element is a dictionary of the kwargs given to the widget's constructor
    - children is an optional element which keys to a dictionary with more TkFire Elements.

    This nestable definition of elements is passed into the constructor as the 'mother'.  Elements
    of the 'mother' can reference the elements of a companion dictionary 'memory' which can store
    tkinter variables and functions to bind to things like buttons.

    Technically, any element keyed by a string which maps to a list will be interpreted as
    [constructor, {arguments}], and so tkinter variables can be specified in the constructor
    of other Elements (see Opt1 in the example below).

    Elements outside TkFire can be accessed via the self.gui dictionary where the path is bang-separated.

    Example::

    | # Defining the memory
    | memory = {
    |     'cmd_continue': lambda: print("Continuing..."),
    |     'var_opt_1': tk.IntVar,
    | }
    |
    | # Defining the mother
    | mother = {
    |     'main_panel': {
    |         layout: ['pack', {'side': 'left', 'fill': 'both', 'ipadx': 3, 'ipady': 3}],
    |         type: ['LabelFrame', {'text': "Left Side", 'width': 16}],
    |         children: {
    |             'Button_01': {
    |                 type: ['Button', {'text': "Play Again", 'command': 'cmd_continue'}],
    |                 layout: ['grid', {'row': 0, 'column': 0}],
    |             },
    |             'Button_02': {
    |                 type: ['Button', {'text': "Quit"}],
    |                 layout: ['grid', {'row': 0, 'column': 0}],
    |             },
    |             'Opt1': {
    |                 TYPE: ['OptionMenu', {'variable': ['var_opt_1', {'value': 0}], 'values': 'options'}],
    |                 LAYOUT: ['pack', TB33],
    |             },
    |         },
    |     ...
    |     }
    |
    | my_core = tk.Tk()
    |
    | # Construct the TkFire object
    | my_ui = TkFire(my_core, mother, memory)
    |
    | # Bind a command to a button after construction
    | my_ui.gui['main_panel!Button_02']['command'] = lambda *_: print("Exiting...")
    | ...
    | my_core.mainloop()
    """

    def __init__(self, core, memory: dict, mother: dict, generator: Dispatcher = None):
        """ Creates a TkFire object which allows a tkinter GUI to be created and modified using dictionary syntax.

        References: :class:`Dispatcher`

        :param core: a tkinter root (Tk, TopLevel, Frame, ...)
        :param memory: a dictionary of variables (keys may be referenced in mother)
        :param mother: a dictionary specifying the GUI
        :param generator: Determines how the objects references in mother will be constructed
        """
        self.core = core
        self.memory = memory
        self._mother = mother

        if generator is None:
            generator = Dispatcher()
        self.generator = generator

        self.gui = dict()  # maps to all widgets
        self._variable_map = dict()  # Whenever variable is bound to a widget,
        # this map stores {name_of_widget_in_gui: name_of_variable_in_memory}

        self._build("", self._mother)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            item = "!".join(item)
        return self.gui[item]

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            key = "!".join(key)
        self.gui[key] = value

    def _build(self, parent, structure):
        """ Constructs the dictionary which contains all the widgets (recursively)

        commits to self.gui

        :param parent: The parent widget
        :param structure: a (sub) dictionary of the mother
        :return: None
        """
        try:
            if parent:
                root = self.gui[parent]
                path = parent + "!"
            else:
                root = self.core
                path = ""
        except Exception as e:
            raise TkFireStructuralError(f"Failed to create path for '{parent}'") from e

        for k, child in structure.items():
            index = path + k

            try:
                kwargs = child[TYPE][1]
            except LookupError as le:
                msg = f"Could not determine Type for '{index}' from:\n{pformat(child, depth=1)}"
                raise TkFireSpecificationError(msg) from le

            args = list()
            has_scrolly = False
            has_scrollx = False

            if 'variable' in kwargs:
                try:
                    var_name, var_spec = kwargs['variable']
                    self.memory[var_name] = self.memory[var_name](root, **var_spec)
                    args.append(self.memory[var_name])
                    del child[TYPE][1]['variable']
                    self._variable_map[index] = var_name
                except Exception as e:
                    msg = f"Could not parse Variable for '{index}' from:\n{pformat(kwargs['variable'])}"
                    raise TkFireSpecificationError(msg) from e

            if 'command' in kwargs:
                try:
                    _command = kwargs['command']
                    if isinstance(_command, str):
                        child[TYPE][1]['command'] = self.memory[kwargs['command']]
                    else:
                        child[TYPE][1]['command'] = _command
                except Exception as e:
                    msg = f"Could not parse Command for '{index}' from:\n{pformat(kwargs['command'])}"
                    raise TkFireSpecificationError(msg) from e

            if 'values' in kwargs:
                try:
                    _values = kwargs['values']
                    if isinstance(_values, str):
                        args += self.memory[kwargs['values']]
                    else:
                        args += _values
                    del child[TYPE][1]['values']
                except Exception as e:
                    msg = f"Could not parse Values for '{index}' from:\n{pformat(kwargs['values'])}"
                    raise TkFireSpecificationError(msg) from e

            try:
                if 'scrolly' in kwargs:
                    has_scrolly = True
                    del child[TYPE][1]['scrolly']
                if 'scrollx' in kwargs:
                    has_scrollx = True
                    del child[TYPE][1]['scrollx']
            except Exception as e:
                msg = f"Could not parse scrollbar for '{index}'"
                raise TkFireSpecificationError(msg) from e

            try:
                self.gui[index] = self.generator.generate(child[TYPE][0], root, *args, **child[TYPE][1])
                getattr(self.gui[index], child[LAYOUT][0])(**child[LAYOUT][1])
            except Exception as e:
                msg = f"Could not build '{index}' from:\n{pformat(child, depth=2)}"
                raise TkFireSpecificationError(msg) from e

            if len(child[TYPE]) == 3:
                for _meta_cmd, _meta_kwargs in child[TYPE][2].items():
                    try:
                        getattr(self.gui[index], _meta_cmd)(**_meta_kwargs)
                    except Exception as e:
                        msg = f"Could not apply meta command to '{index}' from:\n{child[TYPE]}"
                        raise TkFireSpecificationError(msg) from e

            if len(child[LAYOUT]) == 3:
                for _meta_cmd, _meta_kwargs in child[LAYOUT][2].items():
                    try:
                        getattr(root, _meta_cmd)(**_meta_kwargs)
                    except Exception as e:
                        msg = f"Could not apply meta command to parent of '{index}' from:\n{child[LAYOUT]}"
                        raise TkFireSpecificationError(msg) from e

            try:
                if has_scrolly:
                    self.gui[index + '!Scrolly'] = tk.Scrollbar(root)
                    self.gui[index]['yscrollcommand'] = self.gui[index + '!Scrolly'].set
                    self.gui[index + '!Scrolly'].config(command=self.gui[index].yview)
                    self.gui[index + '!Scrolly'].pack(**PACK_SCROLL)
                if has_scrollx:
                    self.gui[index + '!Scrollx'] = tk.Scrollbar(root, orient=tk.HORIZONTAL)
                    self.gui[index]['xscrollcommand'] = self.gui[index + '!Scrollx'].set
                    self.gui[index + '!Scrollx'].config(command=self.gui[index].xview)
                    self.gui[index + '!Scrollx'].pack(**{'side': tk.BOTTOM, 'fill': tk.X})
            except Exception as e:
                msg = f"Could not bind scrollbars for '{index}'"
                raise TkFireSpecificationError(msg) from e

            if CHILDREN in child.keys():
                self._build(index, child[CHILDREN])

    def bind_commands(self, *args):
        """ Binds commands after

        :param args: an iterable of (path, command)
        :return: None
        """
        for (path, _command) in args:
            self.gui[path]['command'] = _command

    def set_optionmenu_options(self, path, options=None, *, variable=None, option_names=None):
        """ Updates the options presented in an OptionMenu

        :param path: The path to the OptionMenu
        :param options: An iterable of options
        :param variable: Which tkinter Variable is modified by the OptionMenu (defaults to that which was originally
          bound to the OptionMenu)
        :param option_names: How the options should be presented in the OptionMenu (defaults to [str(x) for x
          in options])
        :return: None
        """
        option_menu = self[path]['menu']
        option_menu.delete(0, "end")

        if options is None:
            return

        if variable is None:
            var_name = self._variable_map[path]
            variable = self.memory[var_name]

        if option_names is None:
            option_names = [str(opt) for opt in options]
        elif callable(option_names):
            option_names = [option_names(opt) for opt in options]

        for opt, opt_name in zip(options, option_names):  # strict=True
            option_menu.add_command(label=opt_name,
                                    command=lambda value=opt: variable.set(value))

    def destroy(self):
        """ Calls destroy() on the tkinter core

        :return: None
        """
        self.core.destroy()
