"""Controls request rate limiting for API calls."""

import threading
import time

from pydantic import BaseModel, Field, PrivateAttr, model_validator
from typing_extensions import Self

from crewai.utilities.logger import Logger


class RPMController(BaseModel):
    """Manages requests per minute limiting.

    When ``max_rpm`` is set, this controller enforces a ceiling on how many
    API requests are made within a 60-second rolling window.  Callers invoke
    :meth:`check_or_wait` before each request; the method either returns
    immediately (if the limit has not been reached) or blocks until the next
    minute boundary.

    A background :class:`threading.Timer` resets the per-minute counter every
    60 seconds.  Call :meth:`stop_rpm_counter` when the controller is no
    longer needed to prevent the timer from firing after the owning object
    has been garbage-collected.
    """

    max_rpm: int | None = Field(
        default=None,
        description="Maximum requests per minute. If None, no limit is applied.",
    )
    logger: Logger = Field(default_factory=lambda: Logger(verbose=False))
    _current_rpm: int = PrivateAttr(default=0)
    _timer: "threading.Timer | None" = PrivateAttr(default=None)
    _lock: "threading.Lock | None" = PrivateAttr(default=None)
    _shutdown_flag: bool = PrivateAttr(default=False)

    @model_validator(mode="after")
    def reset_counter(self) -> Self:
        """Initialise the RPM counter and start the background reset timer.

        Called automatically by Pydantic after the model is constructed.  When
        ``max_rpm`` is configured and the controller has not been shut down, a
        :class:`threading.Lock` is created and the first reset timer is
        scheduled.

        Returns:
            The fully-initialised :class:`RPMController` instance.
        """
        if self.max_rpm is not None:
            if not self._shutdown_flag:
                self._lock = threading.Lock()
                self._reset_request_count()
        return self

    def check_or_wait(self) -> bool:
        """Allow the next request or block until the current minute window resets.

        If ``max_rpm`` is ``None`` the method returns ``True`` immediately with
        no side effects.  Otherwise it increments the running counter and, if
        the limit has been reached, logs a notice and sleeps until the next
        60-second window before resetting the counter to 1.

        Returns:
            Always ``True`` — either the request was allowed straight away or
            the controller blocked until capacity was available.
        """
        if self.max_rpm is None:
            return True

        def _check_and_increment() -> bool:
            if self.max_rpm is not None and self._current_rpm < self.max_rpm:
                self._current_rpm += 1
                return True
            if self.max_rpm is not None:
                self.logger.log(
                    "info", "Max RPM reached, waiting for next minute to start."
                )
                self._wait_for_next_minute()
                self._current_rpm = 1
                return True
            return True

        if self._lock:
            with self._lock:
                return _check_and_increment()
        else:
            return _check_and_increment()

    def stop_rpm_counter(self) -> None:
        """Stop the RPM counter and cancel any pending reset timer.

        Sets the shutdown flag so that the background timer does not reschedule
        itself after it fires.  Safe to call multiple times.
        """
        self._shutdown_flag = True
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _wait_for_next_minute(self) -> None:
        """Block the calling thread for 60 seconds and reset the RPM counter.

        This is called while the lock is held by :meth:`check_or_wait`, so the
        sleep intentionally holds the lock to prevent other threads from
        issuing requests during the wait period.
        """
        time.sleep(60)
        self._current_rpm = 0

    def _reset_request_count(self) -> None:
        """Reset ``_current_rpm`` to zero and reschedule the next reset.

        Acquires ``_lock`` (if available) before mutating shared state, then
        schedules a daemon :class:`threading.Timer` to call this method again
        in 60 seconds.  Stops rescheduling once ``_shutdown_flag`` is set.
        """
        def _reset() -> None:
            self._current_rpm = 0
            if not self._shutdown_flag:
                self._timer = threading.Timer(60.0, self._reset_request_count)
                self._timer.daemon = True
                self._timer.start()

        if self._lock:
            with self._lock:
                _reset()
        else:
            _reset()
