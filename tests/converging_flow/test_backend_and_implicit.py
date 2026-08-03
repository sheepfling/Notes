from __future__ import annotations

from importlib.util import find_spec

import numpy as np
import pytest

from converging_flow.backend import backend_available, get_array_backend
from converging_flow.implicit import (
    LinearSolverConfig,
    crank_nicolson_diffusion,
    explicit_midpoint_diffusion,
)
from converging_flow.radiant_wave import (
    RadiantWaveConfig,
    initialize_fields,
    resolve_diffusion_method,
    run_radiant_wave,
    stable_timestep,
)


def test_numpy_backend_round_trip() -> None:
    backend = get_array_backend("numpy")
    values = np.arange(12, dtype=np.float64).reshape(3, 4)

    device_values = backend.asarray(values)

    assert backend.name == "numpy"
    assert np.array_equal(backend.to_numpy(device_values), values)
####


def test_auto_backend_resolves_to_an_available_backend() -> None:
    backend = get_array_backend("auto")

    assert backend.name in ("numpy", "cupy")
    assert backend_available(backend.name)
####


def test_missing_cupy_has_clear_error() -> None:
    if find_spec("cupy") is not None:
        pytest.skip("CuPy is installed in this environment")
    ####

    with pytest.raises(RuntimeError, match="optional GPU dependency"):
        get_array_backend("cupy")
    ####
####


def test_crank_nicolson_preserves_constant_field() -> None:
    backend = get_array_backend("numpy")
    values = np.full((20, 16), 3.25, dtype=np.float64)
    coefficient = np.linspace(0.5, 2.0, values.size).reshape(values.shape)

    result = crank_nicolson_diffusion(
        values,
        coefficient,
        (0.1, 0.12),
        0.5,
        backend,
        LinearSolverConfig(relative_tolerance=1.0e-11),
    )

    assert np.allclose(result, values, atol=1.0e-10)
####


def test_crank_nicolson_matches_explicit_for_small_step() -> None:
    backend = get_array_backend("numpy")
    coordinates = np.linspace(-1.0, 1.0, 64, dtype=np.float64)
    values = np.exp(-8.0 * coordinates * coordinates)
    coefficient = np.full_like(values, 0.08)
    timestep = 1.0e-4

    explicit = explicit_midpoint_diffusion(
        values,
        coefficient,
        (coordinates[1] - coordinates[0],),
        timestep,
        backend,
    )
    implicit = crank_nicolson_diffusion(
        values,
        coefficient,
        (coordinates[1] - coordinates[0],),
        timestep,
        backend,
        LinearSolverConfig(relative_tolerance=1.0e-12),
    )

    assert np.allclose(implicit, explicit, rtol=2.0e-6, atol=2.0e-8)
####


def test_implicit_radiant_timestep_is_not_diffusion_limited() -> None:
    explicit_config = RadiantWaveConfig(
        dimensions=1,
        resolution=(512,),
        maximum_timestep=0.1,
        diffusion_method="explicit",
    )
    implicit_config = RadiantWaveConfig(
        dimensions=1,
        resolution=(512,),
        maximum_timestep=0.1,
        diffusion_method="crank-nicolson",
    )
    _coordinates, explicit_materials, *_ = initialize_fields(explicit_config)
    _coordinates, implicit_materials, *_ = initialize_fields(implicit_config)

    explicit_timestep = stable_timestep(explicit_config, explicit_materials)
    implicit_timestep = stable_timestep(implicit_config, implicit_materials)

    assert implicit_timestep > explicit_timestep
####


def test_crank_nicolson_radiant_run_is_finite() -> None:
    config = RadiantWaveConfig(
        dimensions=2,
        resolution=(20, 20),
        final_time=0.02,
        backend="numpy",
        diffusion_method="crank-nicolson",
        maximum_timestep=0.01,
    )

    result = run_radiant_wave(config, snapshot_count=3)

    assert result.resolved_backend == "numpy"
    assert result.time == pytest.approx(config.final_time)
    assert np.all(np.isfinite(result.activity))
    assert np.all(np.isfinite(result.heat))
    assert np.all(np.isfinite(result.wave))
####


def test_auto_diffusion_selects_implicit_only_when_diffusion_dominates() -> None:
    fine_config = RadiantWaveConfig(
        dimensions=1,
        resolution=(512,),
        maximum_timestep=0.1,
        diffusion_method="auto",
    )
    coarse_config = RadiantWaveConfig(
        dimensions=3,
        resolution=(20, 20, 20),
        maximum_timestep=0.1,
        diffusion_method="auto",
    )
    _coordinates, fine_materials, *_ = initialize_fields(fine_config)
    _coordinates, coarse_materials, *_ = initialize_fields(coarse_config)

    assert resolve_diffusion_method(fine_config, fine_materials) == "crank-nicolson"
    assert resolve_diffusion_method(coarse_config, coarse_materials) == "explicit"
####


def test_backend_euler_matches_numpy_reference() -> None:
    from converging_flow.euler import (
        advance_rusanov,
        primitive_to_conservative,
    )
    from converging_flow.euler_backend import (
        advance_rusanov_backend,
        primitive_to_conservative_backend,
    )

    backend = get_array_backend("numpy")
    density = np.linspace(0.9, 1.1, 40, dtype=np.float64)
    velocity = np.zeros((1, 40), dtype=np.float64)
    velocity[0] = np.linspace(-0.1, 0.1, 40)
    pressure = np.linspace(1.05, 0.95, 40, dtype=np.float64)
    gamma = 1.4

    reference_state = primitive_to_conservative(
        density,
        velocity,
        pressure,
        gamma,
    )
    backend_state = primitive_to_conservative_backend(
        density,
        velocity,
        pressure,
        gamma,
        backend,
    )
    reference_next = advance_rusanov(
        reference_state,
        1.0e-3,
        (0.05,),
        gamma,
        1.0e-8,
        1.0e-8,
    )
    backend_next = advance_rusanov_backend(
        backend_state,
        1.0e-3,
        (0.05,),
        gamma,
        1.0e-8,
        1.0e-8,
        backend,
    )

    assert np.allclose(backend.to_numpy(backend_next), reference_next)
####
