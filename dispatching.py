""" Resolution of references in a TkFire Mother object

@author: Richard "Ben" Canty
"""

from tkinter import Variable


NOT_FILLED = type(...)


class Memory(dict):
    """ A dictionary-like container for any variables and values requiring unpacking in a TkFire object's creation

    Getting and Setting are identical to that of a python dictionary (with the exception that __setitem__ returns the
    value)

    The __contains__ method has been modified (a) to integrate with under-the-hood types and (b) to return False
    instead of raising a TypeError when the key in question is not a valid key (i.e., if the key is not a valid
    dictionary key, then this Memory(dict) object does not contain that key).

    Implements vpsec() to allow for the delayed initialization of variables in the GUI and varg() to encode
    that a variable needs to be unpacked.
    """
    def __contains__(self, item):
        if isinstance(item, (VarArg, VarSpec)):
            item = item.name
        try:
            return super(Memory, self).__contains__(item)
        except TypeError:
            return False
    
    def __getitem__(self, item):
        if isinstance(item, (VarArg, VarSpec)):
            item = item.name
        return super(Memory, self).__getitem__(item)
    
    def __setitem__(self, key, value):
        if isinstance(key, (VarArg, VarSpec)):
            key = key.name
        super(Memory, self).__setitem__(key, value)
        return value

    @staticmethod
    def varspec(name, *args, **kwargs):
        """ Tkinter variable specification

        Variables will be constructed via Variable[TYPE](master: tk, *args, **kwargs)

        :param name: The name of the variable (its key in Memory)
        :param args: Positional arguments passed into Memory[name]'s constructor
        :param kwargs: Keyword arguments passed into Memory[name]'s constructor
        """
        return VarSpec(name, *args, **kwargs)

    @staticmethod
    def varg(name: str, unpack=0):
        """ Variable argument specification

        :param name: The name of the variable (its key in Memory)
        :param unpack: The degree of unpacking required (0: foo(bar), 1: foo(*bar), 2: foo(**bar)), must be 0, 1, or 2
        """
        return VarArg(name, unpack)


def spec(constructor, *args, **kwargs):
    """ Helper to specify the args and kwargs of a TYPE in a uniform format

    :param constructor: Constructor to which args and kwargs are passed
    :param args: Positional arguments
    :param kwargs: Keyword Arguments
    :return: (_base_specifier, args, kwargs)
    """
    return constructor, args, kwargs


def post(callable_attribute: str, *args, **kwargs):
    """ Helper to specify the args and kwargs of a post method in a uniform format

    :param callable_attribute: The name of the parent object's attribute to which args and kwargs are passed
    :param args: Positional arguments
    :param kwargs: Keyword Arguments
    :return: (callable_attribute, args, kwargs)
    """
    return spec(callable_attribute, *args, **kwargs)


def fire_grid(row=..., column=..., rowspan=..., columnspan=..., sticky=...,
              padx=..., pady=..., ipadx=..., ipady=..., **kwargs):
    """ Position a widget in the parent widget in a grid.

    :param row: The row to put widget in; default 0 (topmost row)
    :param column: The column to put widget in; default 0 (leftmost column).
    :param rowspan: How many rows the widget occupies; default 1.
    :param columnspan: How many columns the widget occupies; default 1.
    :param sticky: What to do if the cell is larger than widget. By default, with sticky='', widget is centered
      in its cell. sticky may be the string concatenation of zero or more of N, E, S, W, NE, NW, SE, and SW,
      compass directions indicating the sides and corners of the cell to which widget sticks.
    :param padx: How many pixels to pad widget, horizontally, outside v's borders.
    :param pady: How many pixels to pad widget, vertically, outside v's borders.
    :param ipadx: How many pixels to pad widget, horizontally, inside widget's borders.
    :param ipady: How many pixels to pad widget, vertically, inside widget's borders.
    """
    return spec('grid', **_clean_vargin(locals()), **kwargs)


def fire_pack(side=..., fill=..., anchor=..., padx=..., pady=..., ipadx=..., ipady=..., expand=..., **kwargs):
    """ Pack a widget in the parent widget.

    :param side: where to add this widget (TOP or BOTTOM or LEFT or RIGHT)
    :param fill: fill widget if widget grows (NONE or X or Y or BOTH)
    :param anchor: position widget according to given direction (NSEW (or subset))
    :param padx: How many pixels to pad widget, horizontally, outside v's borders.
    :param pady: How many pixels to pad widget, vertically, outside v's borders.
    :param ipadx: How many pixels to pad widget, horizontally, inside widget's borders.
    :param ipady: How many pixels to pad widget, vertically, inside widget's borders.
    :param expand: expand widget if parent size grows
    """
    return spec('pack', **_clean_vargin(locals()), **kwargs)


def fire_place(x=..., y=..., relx=..., rely=..., anchor=...,
               width=..., height=..., relwidth=..., relheight=..., bordermode=..., **kwargs):
    """ Place a widget in the parent widget.

    :param x: locate anchor of this widget at position x of master
    :param y: locate anchor of this widget at position y of master
    :param relx: locate anchor of this widget between 0.0 and 1.0 relative to width
      of master (1.0 is right edge)
    :param rely: locate anchor of this widget between 0.0 and 1.0 relative to height
      of master (1.0 is bottom edge)
    :param anchor: position anchor according to given direction (NSEW (or subset))
    :param width: width of this widget in pixel
    :param height: height of this widget in pixel
    :param relwidth: width of this widget between 0.0 and 1.0 relative to width of
      master (1.0 is the same width as the master)
    :param relheight: height of this widget between 0.0 and 1.0 relative to height of
      master (1.0 is the same height as the master)
    :param bordermode: whether to take border width of master widget into account
      ("inside" or "outside")
    """
    return spec('place', **_clean_vargin(locals()), **kwargs)


def stub():
    """ Helper to indicate that a widget will be specified after build() is called

    :return: spec(Stub)
    """
    return spec(Stub)


# #### Private ####
class Stub:
    def __init__(self, layout_type, layout_args, layout_kwargs):
        self.layout = layout_type, layout_args, layout_kwargs


class VarSpec:
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def construct(self, root, constructor) -> Variable:
        return constructor(root, *self.args, **self.kwargs)


class VarArg:
    def __init__(self, name, unpack=0):
        if not 0 <= unpack <= 2:
            raise ValueError(f"A VarArg's unpack parameter must be between 0 and 2 (inclusive), not {unpack}")

        self.name = name
        self.unpack = unpack


def _clean_vargin(vargs):
    vargs.pop("kwargs", None)
    return {k: v for k, v in vargs.items() if not isinstance(v, NOT_FILLED)}
