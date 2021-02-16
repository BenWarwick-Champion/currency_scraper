from functools import wraps
from time import perf_counter


def measure_perf(func):
    """Print decorated function run time in secs."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = perf_counter()
        result = func(*args, **kwargs)
        t1 = perf_counter()
        print("Request took:", t1 - t0)
        return result
    return wrapper


def send_string(conn, string: str):
    conn.sendall((string + '\n').encode())
