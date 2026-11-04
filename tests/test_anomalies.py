import random

import pytest

from generator.generation.anomalies import AnomalyKind, AnomalyPolicy


def test_policy_never_creates_anomaly_at_zero_probability() -> None:
    policy = AnomalyPolicy(0.0, strength=3.0, rng=random.Random(1))

    assert all(policy.decide() is None for _ in range(20))


def test_policy_always_creates_taxi_anomaly_at_probability_one() -> None:
    policy = AnomalyPolicy(1.0, strength=2.0, rng=random.Random(2))

    assert all(policy.decide() in AnomalyKind for _ in range(20))


def test_policy_is_reproducible_with_seed() -> None:
    first = AnomalyPolicy(0.5, strength=2.0, rng=random.Random(7))
    second = AnomalyPolicy(0.5, strength=2.0, rng=random.Random(7))

    assert [first.decide() for _ in range(20)] == [second.decide() for _ in range(20)]


def test_policy_validates_configuration() -> None:
    with pytest.raises(ValueError):
        AnomalyPolicy(-0.1, strength=1.0, rng=random.Random())
    with pytest.raises(ValueError):
        AnomalyPolicy(0.1, strength=-1.0, rng=random.Random())
