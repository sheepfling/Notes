"""Check the coffee-choice model against the recorded examples and invariants."""

import pytest

from notes.thermal.coffee_choice import Parameters, compare, cool, mix


def test_recorded_default_and_warm_creamer() -> None:
    early, late = compare(Parameters())
    assert early == pytest.approx(33.05, abs=0.005)
    assert late == pytest.approx(31.57, abs=0.005)
    assert late - early == pytest.approx(-1.49, abs=0.005)

    early, late = compare(Parameters(creamer_c=70.0))
    assert early == pytest.approx(34.44, abs=0.005)
    assert late == pytest.approx(34.58, abs=0.005)
    assert late - early == pytest.approx(0.14, abs=0.005)


def test_instant_addition_gives_equal_results() -> None:
    early, late = compare(Parameters(add_later_s=0.0))
    assert early == pytest.approx(late)


def test_cooling_and_mixing_obey_model() -> None:
    assert cool(90, 20, 1045, 3, 0) == pytest.approx(90)
    assert mix(80, 20, 4, 1) == pytest.approx(68)
    with pytest.raises(ValueError):
        compare(Parameters(add_later_s=601))
