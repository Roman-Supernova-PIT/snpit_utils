__all__ = [ 'isSequence', 'parse_bool', 'env_as_bool' ]

import os
import numbers
import collections.abc
import numpy as np


def isSequence( var ):
    """Return True if var is a sequence, but not a string or bytes.

    Todo: figure out other things we want to exclude.

    The goal is to return True if it's a list, tuple, array, or
    something that works like that.

    """
    return ( isinstance( var, np.ndarray ) or
             ( isinstance( var, collections.abc.Sequence )
               and not ( isinstance( var, str ) or
                         isinstance( var, bytes ) )
              )
            )


def parse_bool(text):
    """Check if a value represents a boolean value, and return that boolean value if it does.

    Parameters
    ----------
      text : bool, int, or str
        If bool, return as is.  If int, return bool(text).  If str,
        return True if text.lower() is any of "true", "yes", or "1";
        return False if text.lower() is any of "false", "no", or "0".
        Otherwise, raise an exception.

    Returns
    -------
      bool


    """
    if text is None:
        return False
    if isinstance(text, bool):
        return text
    elif isinstance(text, numbers.Integral ):
        return bool( text )
    elif isinstance( text, str ) and ( text.lower() in ['true', 'yes', '1'] ):
        return True
    elif isinstance( text, str ) and ( text.lower() in ['false', 'no', '0'] ):
        return False
    else:
        raise ValueError(f'Cannot parse boolean value from "{text}" (type {type(text)})')


def env_as_bool( varname ):
    """Parse an environment variable as a boolean."""
    return parse_bool( os.getenv(varname) )
