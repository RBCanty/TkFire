""" A helper module to allow a tkinter GUI to be defined from a dictionary (collapsable in IDE) with the ability to
reference components by Name.

@author: Richard "Ben" Canty
"""

import tkinter as tk
from dispatching import *
from fire_exceptions import *
from pprint import pformat


__all__ = ["TkFire", "Memory", "spec", "post", "stub",
           "fire_pack", "fire_place", "fire_grid",
           "LAYOUT", "TYPE", "CHILDREN", "POST"]


# #### Constants #### #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #
LAYOUT = 'LAYOUT'
TYPE = 'TYPE'
CHILDREN = 'CHILDREN'
POST = 'POST'

SY = 'scrolly'
SX = 'scrollx'


# #### TkFire #### #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

class TkFire:
    """ A Wrapper for tkinter for a nicer experience in an IDE

    Elements of the GUI are of the form {name: {type: spec, layout: spec, children: {}, post: []}}

    - name will define how the element is referenced in the self.gui dictionary
    - type keys to a specification in the form of a list [Constructor: Type, args: Tuple, kwargs: Dict]
      whose first element is the constructor for a Widget (e.g. LabelFrame, Button) and whose
      second and third elements are the args (packed as a tuple) and the kwargs (packed as a dictionary)
      for the constructor (they are unpacked for the call).  The spec() method is provided to make this
      more concise and mirror normal python syntax.  If {type: stub()}, a stub entry will be made in the
      self.gui dictionary and the build_stub() method can be called to create the widget later and automatically
      manage the geometry of the widget as specified in mother.  A Stub cannot accept any POST items---they will
      be ignored---and will not connect to any scrollbars.
      but an entry will be made into the self.gui dictionary
    - layout is an optional element which keys to a fire_pack, fire_place, or fire_grid call which mimics
      tkinter's geometry managers in a manner compatible with TkFire.  These methods are wrappers for the
      spec() method which explicit and annotated arguments.  The proper syntax to not manage the geometry
      of a widget is to omit the layout key, specifying {layout: spec(None)} is unnecessary and specifying
      {layout: None} will cause an error.
    - children is an optional element which keys to a dictionary with more TkFire Elements.
    - post is an optional element listing operations to be executed after the creation of the Object
      which is a list of lists of the form [[attribute: string, args: Tuple, kwargs: Dict], ...] where
      attribute is an attribute of the parent (the object created just before) which is called with args
      and kwargs (they are unpacked for the call).  The spec() method is provided to make this
      more concise and mirror normal python syntax.

    This nestable definition of elements is passed into the constructor as the 'mother'.  Elements
    of the 'mother' can reference the elements of a companion Memory object 'memory' which can store
    tkinter variables and functions to bind to things like buttons.

    Elements outside TkFire can be accessed via the self.gui dictionary where the path is a
    bang-separated sequence of names (e.g. "level_1!subsection_A!ok_button")

    Outline::

    | # Define the memory
    | memory = Memory(...)
    |
    | # Define the mother
    | mother = {...}
    |
    | # Create a tkinter environment and construct the TkFire object
    | my_core = tk.Tk()
    | my_ui = TkFire(my_core, mother, memory).build()
    |
    | # Run
    | my_core.mainloop()
    """

    def __init__(self, core, memory=None, mother: dict = None):
        """ Creates a TkFire object which allows a tkinter GUI to be created and modified using dictionary syntax.

        References: :class:`Memory`

        :param core: a tkinter root (Tk, TopLevel, Frame, ...)
        :param memory: a dictionary or Memory of variables (keys may be referenced by mother)
        :param mother: a dictionary specifying the GUI
        """
        self.core = core

        if memory is None:
            memory = {}
        if isinstance(memory, Memory):
            self.memory = memory
        else:
            self.memory = Memory(memory)

        if mother is None:
            mother = {}

        self._mother = mother

        self.gui = dict()  # maps to all widgets
        self._variable_map = dict()  # Whenever variable is bound to a widget,
        # this map stores {name_of_widget_in_gui: name_of_variable_in_memory}

    def __getitem__(self, item):
        if isinstance(item, tuple):
            item = "!".join(item)
        return self.gui[item]

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            key = "!".join(key)
        self.gui[key] = value

    # Private

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
            elif value in self.memory:
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
            elif value in self.memory:
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

    def _validate_specifications(self, root, child_spec, child_path, child_repr):
        # Load in constructors and scripts
        try:
            widget_type, widget_args, widget_kwargs = child_spec[TYPE]
            layout_type, layout_args, layout_kwargs = child_spec.get(LAYOUT, [None, (), {}])
            post_methods = child_spec.get(POST, [])
            grandchildren = child_spec.get(CHILDREN, None)
        except (LookupError, TypeError, ValueError) as pe:
            msg = f"Could not parse '{child_path}' from:\n{child_repr}"
            raise TkFireParseError(msg) from pe

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

        return widget_type, widget_args, widget_kwargs, \
            layout_type, layout_args, layout_kwargs, \
            post_methods, grandchildren

    @staticmethod
    def _get_scrolls(args, kwargs, child_path):
        try:
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
        except Exception as e:
            msg = f"Could not parse scrollbar for '{child_path}'"
            raise TkFireSpecificationError(msg) from e

        return has_scroll_y, has_scroll_x

    def _bind_scrolls(self, root, child_path, has_scroll_y, has_scroll_x):
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

    def _generate(self, root, child_path, child_repr, generator, *args, **kwargs):
        try:
            self.gui[child_path] = generator(root, *args, **kwargs)
        except Exception as e:
            msg = f"Could not build '{child_path}' from:\n{child_repr}"
            raise TkFireRenderError(msg) from e

    def _render(self, child_path, layout_type, layout_args, layout_kwargs, child_repr):
        if not layout_type:
            return

        try:
            geometry_manager = getattr(self.gui[child_path], layout_type)
            return geometry_manager(*layout_args, **layout_kwargs)
        except Exception as e:
            msg = f"Could not render '{child_path}' from:\n{child_repr}"
            raise TkFireRenderError(msg) from e

    def _execute_post(self, post_method, method_args, method_kwargs, root, child_path):
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

            widget_type, widget_args, widget_kwargs, \
                layout_type, layout_args, layout_kwargs, \
                post_methods, \
                grandchildren = \
                self._validate_specifications(root, child_spec, child_path, child_repr)

            if widget_type is Stub:
                self.gui[child_path] = Stub(layout_type, layout_args, layout_kwargs)
                continue

            # Set flags for handling scrollbars
            has_scroll_y, has_scroll_x = self._get_scrolls(widget_args, widget_kwargs, child_path)

            # Build the object
            self._generate(root, child_path, child_repr, widget_type, *widget_args, **widget_kwargs)

            # Define its layout
            self._render(child_path, layout_type, layout_args, layout_kwargs, child_repr)

            # Execute post operations:
            for post_method, method_args, method_kwargs in post_methods:
                self._execute_post(post_method, method_args, method_kwargs, root, child_path)

            self._bind_scrolls(root, child_path, has_scroll_y, has_scroll_x)

            self._build(child_path, grandchildren)

    # Main

    def build(self):
        self._build("", self._mother)
        return self

    def bind_commands(self, *args):
        """ Binds commands after build() is called. Calls self.bind_command() on each tuple passed

        :param args: An iterable with elements of the form (path, command)
        :return: None
        """
        for (path, command) in args:
            self.bind_command(path, command)

    def bind_command(self, path, command):
        """ Binds a command to a Button (or other Widget with a 'command' component) after build() is called

        :param path: The gui path to the Widget (e.g. "main!left!button_5")
        :param command: The callable being bound to the command component
        """
        self.gui[path]['command'] = command

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

    def build_stub(self, path, generator, *args, **kwargs):
        """ Converts a stub into real object.

        The parent widget (master) is calculated here, and so should not be included in the args parameter.

        :param path: The gui path to the Widget (e.g. "main!left!button_5")
        :param generator: The constructor for the Widget
        :param args: Positional arguments to be passed to the generator
        :param kwargs: Keyword arguments to be passed to the generator
        :return: The new widget
        """
        widget: Stub = self.gui[path]
        layout_type, layout_args, layout_kwargs = widget.layout

        parent_path, _ = path.rsplit("!", 1)
        parent = self.gui[parent_path]

        self._generate(parent, path, f"{generator} called with args={args}, kwargs={kwargs}",
                       generator, *args, **kwargs)

        getattr(self.gui[path], layout_type)(*layout_args, **layout_kwargs)

        return self.gui[path]

    # tikinter

    def destroy(self):
        """ Calls destroy() on the tkinter core

        :return: None
        """
        self.core.destroy()

    def pack(self, *args, **kwargs):
        self.core.pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        self.core.grid(*args, **kwargs)
