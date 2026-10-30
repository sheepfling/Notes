from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from converging_flow.reaction_diffusion import (
    ReactionDiffusionConfig,
    neumann_laplacian,
    run_reaction_diffusion,
)
from converging_flow.reaction_output import save_reaction_result
from converging_flow.reaction_plotting import (
    save_reaction_animations,
    save_reaction_plots,
)


@pytest.mark.parametrize("dimensions", [1, 2, 3])
def test_constant_field_has_zero_neumann_laplacian(dimensions: int) -> None:
    shape = (12,) * dimensions
    values = np.full(shape, 3.5, dtype=np.float64)
    spacing = (0.1,) * dimensions

    result = neumann_laplacian(values, spacing)

    assert np.allclose(result, 0.0)
####


def test_neumann_laplacian_does_not_wrap_between_domain_edges() -> None:
    values = np.zeros(16, dtype=np.float64)
    values[0] = 1.0

    result = neumann_laplacian(values, (1.0,))

    assert result[-1] == pytest.approx(0.0)
    assert result[1] > 0.0
####


@pytest.mark.parametrize("dimensions,resolution", [(1, 64), (2, 28), (3, 14)])
def test_reaction_fields_remain_finite_and_bounded(
    dimensions: int,
    resolution: int,
) -> None:
    config = ReactionDiffusionConfig(
        dimensions=dimensions,  # type: ignore[arg-type]
        resolution=(resolution,) * dimensions,
        final_time=0.04,
    )

    result = run_reaction_diffusion(config, snapshot_count=3)

    assert result.time == pytest.approx(config.final_time)
    assert len(result.frames) == 3
    assert np.all(np.isfinite(result.activity))
    assert np.all(np.isfinite(result.heat))
    assert np.all(np.isfinite(result.wave))
    assert np.all((0.0 <= result.activity) & (result.activity <= 1.0))
    assert np.all(result.heat >= 0.0)
####


def test_reaction_output_and_visualizations(tmp_path: Path) -> None:
    config = ReactionDiffusionConfig(
        dimensions=2,
        resolution=(24, 24),
        final_time=0.02,
    )
    result = run_reaction_diffusion(config, snapshot_count=3)

    save_reaction_result(result, tmp_path)
    save_reaction_plots(result, tmp_path)
    save_reaction_animations(result, tmp_path, fps=4)

    with np.load(tmp_path / "reaction_state.npz") as payload:
        assert payload["activity"].shape == (24, 24)
        assert payload["frame_activity"].shape == (3, 24, 24)
    ####

    assert (tmp_path / "reaction_summary.json").is_file()
    assert (tmp_path / "activity.png").is_file()
    assert (tmp_path / "activity_evolution.gif").is_file()
####


@pytest.mark.parametrize(
    "dimensions,resolution",
    [(1, 48), (2, 20), (3, 10)],
)
def test_numba_backend_matches_numpy_backend(
    dimensions: int,
    resolution: int,
) -> None:
    pytest.importorskip("numba")
    common = {
        "dimensions": dimensions,
        "resolution": (resolution,) * dimensions,
        "final_time": 0.006,
    }
    numpy_result = run_reaction_diffusion(
        ReactionDiffusionConfig(**common, backend="numpy"),  # type: ignore[arg-type]
    )
    numba_result = run_reaction_diffusion(
        ReactionDiffusionConfig(**common, backend="numba"),  # type: ignore[arg-type]
    )

    assert numba_result.steps == numpy_result.steps
    assert np.allclose(numba_result.activity, numpy_result.activity, atol=1.0e-12)
    assert np.allclose(numba_result.heat, numpy_result.heat, atol=1.0e-12)
    assert np.allclose(numba_result.wave, numpy_result.wave, atol=1.0e-12)
    assert np.allclose(
        numba_result.wave_velocity,
        numpy_result.wave_velocity,
        atol=1.0e-12,
    )
####
