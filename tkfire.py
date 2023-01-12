""" A helper module to allow a tkinter GUI to be defined from a dictionary (collapsable in IDE) with the ability to
reference components by Name.

@author: Richard "Ben" Canty
"""

import tkinter as tk
from dispatching import *
from fire_exceptions import *
from pprint import pformat


# #### Constants #### #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #
LAYOUT = 'LAYOUT'
TYPE = 'TYPE'
CHILDREN = 'CHILDREN'
POST = 'POST'

SY = 'scrolly'
SX = 'scrollx'


# #### Helper Methods #### #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #
def has_key(_d, _key):
    present = False

    if isinstance(_key, VarArg):
        _key = _key.name

    try:
        present = _key in _d
    except TypeError:
        pass
    finally:
        return present


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


# #### TkFire #### #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

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

    def build(self):
        self._build("", self._mother)
        return self

    def __getitem__(self, item):
        if isinstance(item, tuple):
            item = "!".join(item)
        return self.gui[item]

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            key = "!".join(key)
        self.gui[key] = value

    def _sanitize_kwargs(self, kwargs, path, root):
        replacer = list()
        for keyword, value in kwargs.items():
            # value is a constructor  # [ e.g. variable=VarSpec("Opt_1", value=0) ]
            if isinstance(value, VarSpec):
                var_name = value.name
                self._variable_map[path] = var_name
                self.memory[var_name] = value.construct(root, self.memory[var_name])
                replacer.append((keyword, self.memory[var_name]))
            # value is a reference  # [ e.g. values='options' ]
            elif has_key(self.memory, value):
                replacer.append((keyword, self.memory[value]))
            # value is a literal  # [ e.g. values=[1, 2, 3, 4] ]
            else:
                pass
        for keyword, value in replacer:
            kwargs[keyword] = value

    def _sanitize_args(self, args, kwargs, path, root):
        new_args = list()
        for value in args:
            # value is a constructor
            # e.g. foo(..., VarSpec("Opt_1", value=0), ...)
            if isinstance(value, VarSpec):
                var_name = value.name
                self._variable_map[path] = var_name
                self.memory[var_name] = value.construct(root, self.memory[var_name])
                new_args.append(self.memory[var_name])
            # value is a reference
            # e.g. foo(..., 'options', ...)
            elif has_key(self.memory, value):
                if isinstance(value, VarArg):
                    if value.unpack == 2:
                        for k, v in self.memory[value.name]:
                            kwargs.setdefault(k, v)
                    elif value.unpack == 1:
                        for v in self.memory[value.name]:
                            new_args.append(v)
                    else:
                        new_args.append(self.memory[value.name])
                else:
                    new_args.append(self.memory[value])
            # value is a literal
            # e.g. foo(..., [1, 2, 3, 4], ...)
            else:
                new_args.append(value)
        return new_args

    @staticmethod
    def _get_scrolls(args, kwargs):
        if SY in kwargs:
            has_scroll_y = True
            kwargs.pop(SY)
        elif SY in args:
            has_scroll_y = True
            args.pop(args.index(SY))
        else:
            has_scroll_y = False

        if SX in kwargs:
            has_scroll_x = True
            kwargs.pop(SX)
        elif SX in args:
            has_scroll_x = True
            args.pop(args.index(SX))
        else:
            has_scroll_x = False

        return has_scroll_y, has_scroll_x

    def _build(self, parent, structure):
        """ Constructs the dictionary which contains all the widgets (recursively)

        commits to self.gui

        :param parent: The parent widget
        :param structure: a (sub) dictionary of the mother
        :return: None
        """
        if not structure:
            return

        # construct the path and load the parent widget
        try:
            if parent:
                root = self.gui[parent]
                path = parent + "!"
            else:
                root = self.core
                path = ""
        except Exception as e:
            raise TkFireStructuralError(f"Failed to create path for '{parent}'") from e

        # For each widget...
        for child_name, child_spec in structure.items():
            child_path = path + child_name
            child_repr = pformat(child_spec, depth=3)

            # Load in constructors and scripts
            try:
                widget_type, widget_args, widget_kwargs = child_spec[TYPE]
                layout_type, layout_args, layout_kwargs = child_spec[LAYOUT]
                post_methods = child_spec.get(POST, [])
                grandchildren = child_spec.get(CHILDREN, None)
            except LookupError as le:
                msg = f"Could not parse '{child_path}' from:\n{child_repr}"
                raise TkFireParseError(msg) from le

            # Remap names in args:
            try:
                widget_args = self._sanitize_args(widget_args, widget_kwargs, child_path, root)
            except Exception as e:
                msg = f"Could not parse positional arguments for {child_path}'s type from:\n{widget_args}"
                raise TkFireSpecificationError(msg) from e
            try:
                layout_args = self._sanitize_args(layout_args, layout_kwargs, child_path, root)
            except Exception as e:
                msg = f"Could not parse positional arguments for {child_path}'s layout from:\n{layout_args}"
                raise TkFireSpecificationError(msg) from e

            # Remap names in kwargs
            try:
                self._sanitize_kwargs(widget_kwargs, child_path, root)
            except Exception as e:
                msg = f"Could not parse keyword arguments for {child_path}'s type from:\n{widget_kwargs}"
                raise TkFireSpecificationError(msg) from e
            try:
                self._sanitize_kwargs(layout_kwargs, child_path, root)
            except Exception as e:
                msg = f"Could not parse keyword arguments for {child_path}'s layout from:\n{layout_kwargs}"
                raise TkFireSpecificationError(msg) from e

            # Set flags for handling scrollbars
            try:
                has_scroll_y, has_scroll_x = self._get_scrolls(widget_args, widget_kwargs)
            except Exception as e:
                msg = f"Could not parse scrollbar for '{child_path}'"
                raise TkFireSpecificationError(msg) from e

            # Build the object
            try:
                self.gui[child_path] = self.generator.generate(widget_type, root, *widget_args, **widget_kwargs)
            except Exception as e:
                msg = f"Could not build '{child_path}' from:\n{child_repr}"
                raise TkFireRenderError(msg) from e
            # Define its layout
            try:
                getattr(self.gui[child_path], layout_type)(*layout_args, **layout_kwargs)
            except Exception as e:
                msg = f"Could not render '{child_path}' from:\n{child_repr}"
                raise TkFireRenderError(msg) from e

            # Execute post operations:
            for post_method, method_args, method_kwargs in post_methods:
                try:
                    method_args = self._sanitize_args(method_args, method_kwargs, child_path, root)
                except Exception as e:
                    msg = f"Could not parse positional arguments for {child_path}'s post operation:\n{post_method}"
                    raise TkFirePostError(msg) from e
                try:
                    self._sanitize_kwargs(method_kwargs, child_path, root)
                except Exception as e:
                    msg = f"Could not parse keyword arguments for {child_path}'s type operation:\n{post_method}"
                    raise TkFirePostError(msg) from e
                try:
                    getattr(self.gui[child_path], post_method)(*method_args, **method_kwargs)
                except Exception as e:
                    msg = f"Could not execute post method {post_method} specified in '{child_path}'"
                    raise TkFirePostError(msg) from e

            try:
                if has_scroll_y:
                    self.gui[child_path + '!Scrolly'] = tk.Scrollbar(root)
                    self.gui[child_path]['yscrollcommand'] = self.gui[child_path + '!Scrolly'].set
                    self.gui[child_path + '!Scrolly'].config(command=self.gui[child_path].yview)
                    self.gui[child_path + '!Scrolly'].pack(side=tk.RIGHT, fill=tk.Y)
                if has_scroll_x:
                    self.gui[child_path + '!Scrollx'] = tk.Scrollbar(root, orient=tk.HORIZONTAL)
                    self.gui[child_path]['xscrollcommand'] = self.gui[child_path + '!Scrollx'].set
                    self.gui[child_path + '!Scrollx'].config(command=self.gui[child_path].xview)
                    self.gui[child_path + '!Scrollx'].pack(side=tk.BOTTOM, fill=tk.X)
            except Exception as e:
                msg = f"Could not bind scrollbars for '{child_path}'"
                raise TkFireSpecificationError(msg) from e

            self._build(child_path, grandchildren)

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

    def pack(self, *args, **kwargs):
        self.core.pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        self.core.grid(*args, **kwargs)
