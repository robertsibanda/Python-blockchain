from typing import Callable


def authenticated(func: Callable):
    def wrapper(*args, **kwargs):
        print("Arguments : ", args)
        return func(*args, **kwargs)

    return wrapper
