import pytest

from generator.retry import RetryError, RetryPolicy


def test_retry_succeeds_after_transient_failures() -> None:
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("temporary failure")
        return "ok"

    policy = RetryPolicy(5, 0.0, 1.0, sleep=lambda _: None)

    assert policy.execute(operation) == "ok"
    assert len(calls) == 3


def test_retry_raises_after_last_attempt() -> None:
    def operation() -> None:
        raise ConnectionError("database is unavailable")

    policy = RetryPolicy(2, 0.0, 1.0, sleep=lambda _: None)

    with pytest.raises(RetryError):
        policy.execute(operation)


def test_retry_backoff_is_capped() -> None:
    delays: list[float] = []
    policy = RetryPolicy(
        4,
        base_delay=1.0,
        max_delay=2.0,
        backoff_factor=2.0,
        jitter=0.0,
        sleep=delays.append,
    )

    with pytest.raises(RetryError):
        policy.execute(lambda: (_ for _ in ()).throw(ConnectionError("failure")))

    assert delays == [1.0, 2.0, 2.0]
