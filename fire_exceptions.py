""" Contains the exceptions which can be raised by TkFire

TODO: incorporate the ability to construct from a caught exception to provide more useful (and concise) traceback

@author: Richard "Ben" Canty
"""


class TkFireStructuralError(Exception):
    pass


class TkFireSpecificationError(Exception):
    pass


class TkFireParseError(Exception):
    pass


class TkFireRenderError(Exception):
    pass


class TkFirePostError(Exception):
    pass
