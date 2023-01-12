""" Resolution of references in a TkFire Mother object

@author: Richard "Ben" Canty
"""

import tkinter as tk
from tkinter import scrolledtext as st
from tkinter import ttk


class Memory(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def __contains__(self, item):
        super().__contains__(item)
    
    def __getitem__(self, item):
        super().__getitem__(item)
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
    

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


def spec(_base_specifier, /, *args, **kwargs):
    """ Helper to specify the args and kwargs of a method in a uniform format

    :param _base_specifier: Method or Name to which args and kwargs are passed
    :param args: Positional arguments
    :param kwargs: Keyword Arguments
    :return: (args, kwargs)
    """
    return _base_specifier, args, kwargs


class VarSpec:
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def construct(self, root, constructor) -> tk.Variable:
        return constructor(root, *self.args, **self.kwargs)


class VarArg:
    def __init__(self, name, unpack=0):
        if not 0 <= unpack <= 2:
            raise ValueError(f"A VarArg's unpack parameter must be between 0 and 2 (inclusive), not {unpack}")

        self.name = name
        self.unpack = unpack
