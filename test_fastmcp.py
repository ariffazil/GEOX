import inspect
import functools

def original(a: int, b: str = "hi"):
    pass

@functools.wraps(original)
def wrapper(*args, **kwargs):
    pass

print(inspect.signature(wrapper))
