"""One monotonic budget shared by all operations in an HTTP request."""

from contextvars import ContextVar, copy_context
from dataclasses import dataclass, field
from threading import BoundedSemaphore, Event, Thread
from time import monotonic
import time


class DeadlineExceeded(TimeoutError):
    pass


@dataclass
class Deadline:
    expires: float
    cancelled: Event = field(default_factory=Event)

    def remaining(self) -> float:
        value = self.expires - monotonic()
        if self.cancelled.is_set() or value <= 0:
            raise DeadlineExceeded("Interview request deadline exceeded")
        return value


current_deadline = ContextVar("interview_deadline", default=None)
# A timed-out synchronous transport cannot be forcibly killed. Keep its slot
# until it actually exits, so abandoned calls cannot create unlimited threads.
_transport_slots = BoundedSemaphore(16)


def remaining(cap: float) -> float:
    deadline = current_deadline.get()
    return min(cap, deadline.remaining()) if deadline else cap


def check() -> None:
    remaining(float("inf"))


def pause(seconds: float) -> None:
    deadline = current_deadline.get()
    if deadline:
        delay = remaining(seconds)
        deadline.cancelled.wait(delay)
        if delay < seconds:
            raise DeadlineExceeded("Interview request deadline exceeded")
        check()
    else:
        time.sleep(seconds)


def provider_call(operation, timeout: float):
    """Bound wall time as well as the SDK's socket inactivity timeout."""
    timeout = remaining(timeout)
    if not _transport_slots.acquire(blocking=False):
        raise RuntimeError("Provider transport capacity exhausted")
    done = Event()
    outcome = []
    context = copy_context()

    def invoke():
        check()
        return operation()

    def run():
        try:
            outcome.append((True, context.run(invoke)))
        except BaseException as exc:
            outcome.append((False, exc))
        finally:
            _transport_slots.release()
            done.set()

    Thread(target=run, daemon=True).start()
    if not done.wait(timeout):
        check()
        raise TimeoutError("Provider call timed out")
    check()
    success, result = outcome[0]
    if not success:
        raise result
    return result
