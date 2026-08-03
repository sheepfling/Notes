from __future__ import annotations

from pathlib import Path

import numpy as np

from converging_flow.config import SimulationConfig
from converging_flow.experiment import run_simulation
from converging_flow.output import save_result
from converging_flow.plotting import save_animations, save_plots


def test_frame_output_and_visualizations(tmp_path: Path) -> None:
    config = SimulationConfig(
        dimensions=1,
        resolution=(48,),
        final_time=0.01,
    )
    result = run_simulation(config, snapshot_count=3)

    save_result(result, tmp_path)
    save_plots(result, tmp_path)
    save_animations(result, tmp_path, fps=4)

    with np.load(tmp_path / "state.npz") as payload:
        assert payload["frame_time"].shape == (3,)
        assert payload["frame_density"].shape == (3, 48)
        assert payload["frame_radial_velocity"].shape == (3, 128)
    ####

    assert (tmp_path / "density.png").is_file()
    assert (tmp_path / "radial_velocity_profile.png").is_file()
    assert (tmp_path / "density_evolution.gif").is_file()
    assert (tmp_path / "radial_density_evolution.gif").is_file()
####
