"""What an agent did while answering one request: its model calls, the tools
it used, and what Agent Manager blocked. The page shows these steps next to
the answer."""
import contextvars

_steps = contextvars.ContextVar("steps", default=None)
# Some frameworks work in threads of their own, which do not see the request's
# context: their steps go to the request in progress.
_active = []


def start():
    """Starts a fresh list for the current request and returns it."""
    global _active
    _active = []
    _steps.set(_active)
    return _active


def record(kind, **data):
    steps = _steps.get()
    (steps if steps is not None else _active).append({"kind": kind, **data})
