""" Contains the exceptions which can be raised by TkFire

TODO: incorporate the ability to construct from a caught exception to provide more useful (and concise) traceback

@author: Richard "Ben" Canty
"""
import traceback


class TkFireException(Exception):
    pass


class TkFireStructuralError(TkFireException):
    pass


class TkFireSpecificationError(TkFireException):
    pass


class TkFireParseError(TkFireException):
    pass


class TkFireRenderError(TkFireException):
    pass


class TkFirePostError(TkFireException):
    pass
