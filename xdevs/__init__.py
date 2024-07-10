from __future__ import annotations
import functools
import logging
import math
import sys
from typing import TypeVar
import warnings

T = TypeVar('T')

INFINITY: float = math.inf
PHASE_PASSIVE: str = "passive"
PHASE_ACTIVE: str = "active"

DEBUG_LEVEL: int | str | None = None
LOGGERS: dict[str, logging.Logger] = dict()


def get_logger(name: str, dl: int | str = None):
    if name in LOGGERS:
        return LOGGERS[name]
    else:
        logger = logging.getLogger(name)

        if dl or DEBUG_LEVEL:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(dl or DEBUG_LEVEL)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
        else:
            logger.disabled = True

        LOGGERS[name] = logger
        return logger


def deprecated(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn(f"Call to deprecated function {func.__name__}.", category=DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)
    return new_func
