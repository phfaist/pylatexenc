
def partial(fn, *args, **kwargs):
    return lambda *newargs, **newkwargs: fn(*args, *newargs, **dict(kwargs, **newkwargs))
