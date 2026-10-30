"""Compatibility entrypoint for the coffee article's co-located tests.

The historical ``python -m pytest tests/thermal`` command remains supported.
The canonical tests live next to the article in ``notes/thermal/tests``.
"""

from notes.thermal.tests.test_coffee_article import (
    test_cooling_and_mixing_obey_model,
    test_instant_addition_gives_equal_results,
    test_module_reproduction_prints_results_without_artifacts,
    test_recorded_default_and_warm_creamer,
)

__all__ = [
    "test_cooling_and_mixing_obey_model",
    "test_instant_addition_gives_equal_results",
    "test_module_reproduction_prints_results_without_artifacts",
    "test_recorded_default_and_warm_creamer",
]
