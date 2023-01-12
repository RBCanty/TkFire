""" Contains the exceptions which can be raised by TkFire

TODO: incorporate the ability to construct from a caught exception to provide more useful (and concise) traceback

@author: Richard "Ben" Canty
"""
import traceback


class TkFireException(Exception):
    def __init__(self, base, *, message="", context=None):
        self.__cause__ = base
        self.args = (message, *self.args, context)


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


if __name__ == '__main__':
    from pprint import pprint

    try:
        a = 4/0
    except Exception as e:
        try:
            raise TkFireException(e, message="This is an exception", context="It occurred here")
        except TkFireException as tkfe:
            raise TkFireException(tkfe, message="Level 2")
