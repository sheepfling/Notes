from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numba import njit, prange

if TYPE_CHECKING:
    from converging_flow.reaction_diffusion import (
        FloatArray,
        ReactionDiffusionConfig,
    )


@njit(cache=True, fastmath=True)
def _advance_1d(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    wave_velocity: FloatArray,
    local_growth: FloatArray,
    local_loss: FloatArray,
    activity_diffusivity: float,
    heat_diffusivity: float,
    heat_feedback: float,
    heat_source_rate: float,
    heat_decay_rate: float,
    wave_speed_squared: float,
    wave_source_rate: float,
    wave_damping: float,
    inverse_dx_squared: float,
    timestep: float,
    midpoint_activity: FloatArray,
    midpoint_heat: FloatArray,
    midpoint_wave: FloatArray,
    midpoint_wave_velocity: FloatArray,
) -> None:
    size = activity.shape[0]
    half_timestep = 0.5 * timestep

    for index in range(size):
        lower = 0 if index == 0 else index - 1
        upper = size - 1 if index == size - 1 else index + 1

        activity_value = activity[index]
        heat_value = heat[index]
        wave_value = wave[index]
        velocity_value = wave_velocity[index]

        activity_laplacian = (
            activity[lower] - 2.0 * activity_value + activity[upper]
        ) * inverse_dx_squared
        heat_laplacian = (
            heat[lower] - 2.0 * heat_value + heat[upper]
        ) * inverse_dx_squared
        wave_laplacian = (
            wave[lower] - 2.0 * wave_value + wave[upper]
        ) * inverse_dx_squared

        saturation = max(1.0 - activity_value, 0.0)
        activity_rate = (
            activity_diffusivity * activity_laplacian
            + local_growth[index] * activity_value * saturation
            + heat_feedback * heat_value * saturation
            - local_loss[index] * activity_value
        )
        heat_rate = (
            heat_diffusivity * heat_laplacian
            + heat_source_rate * activity_value
            - heat_decay_rate * heat_value
        )
        wave_velocity_rate = (
            wave_speed_squared * wave_laplacian
            + wave_source_rate * activity_value
            - wave_damping * velocity_value
        )

        midpoint_activity[index] = min(
            max(activity_value + half_timestep * activity_rate, 0.0),
            1.0,
        )
        midpoint_heat[index] = max(
            heat_value + half_timestep * heat_rate,
            0.0,
        )
        midpoint_wave[index] = wave_value + half_timestep * velocity_value
        midpoint_wave_velocity[index] = (
            velocity_value + half_timestep * wave_velocity_rate
        )
    ####

    for index in range(size):
        lower = 0 if index == 0 else index - 1
        upper = size - 1 if index == size - 1 else index + 1

        activity_value = midpoint_activity[index]
        heat_value = midpoint_heat[index]
        wave_value = midpoint_wave[index]
        velocity_value = midpoint_wave_velocity[index]

        activity_laplacian = (
            midpoint_activity[lower]
            - 2.0 * activity_value
            + midpoint_activity[upper]
        ) * inverse_dx_squared
        heat_laplacian = (
            midpoint_heat[lower] - 2.0 * heat_value + midpoint_heat[upper]
        ) * inverse_dx_squared
        wave_laplacian = (
            midpoint_wave[lower] - 2.0 * wave_value + midpoint_wave[upper]
        ) * inverse_dx_squared

        saturation = max(1.0 - activity_value, 0.0)
        activity_rate = (
            activity_diffusivity * activity_laplacian
            + local_growth[index] * activity_value * saturation
            + heat_feedback * heat_value * saturation
            - local_loss[index] * activity_value
        )
        heat_rate = (
            heat_diffusivity * heat_laplacian
            + heat_source_rate * activity_value
            - heat_decay_rate * heat_value
        )
        wave_velocity_rate = (
            wave_speed_squared * wave_laplacian
            + wave_source_rate * activity_value
            - wave_damping * velocity_value
        )

        activity[index] = min(
            max(activity[index] + timestep * activity_rate, 0.0),
            1.0,
        )
        heat[index] = max(heat[index] + timestep * heat_rate, 0.0)
        wave[index] += timestep * velocity_value
        wave_velocity[index] += timestep * wave_velocity_rate
    ####
####


@njit(cache=True, fastmath=True, parallel=True)
def _advance_2d(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    wave_velocity: FloatArray,
    local_growth: FloatArray,
    local_loss: FloatArray,
    activity_diffusivity: float,
    heat_diffusivity: float,
    heat_feedback: float,
    heat_source_rate: float,
    heat_decay_rate: float,
    wave_speed_squared: float,
    wave_source_rate: float,
    wave_damping: float,
    inverse_dx_squared: float,
    inverse_dy_squared: float,
    timestep: float,
    midpoint_activity: FloatArray,
    midpoint_heat: FloatArray,
    midpoint_wave: FloatArray,
    midpoint_wave_velocity: FloatArray,
) -> None:
    size_x, size_y = activity.shape
    cell_count = size_x * size_y
    half_timestep = 0.5 * timestep

    for flat_index in prange(cell_count):
        index_x = flat_index // size_y
        index_y = flat_index - index_x * size_y

        lower_x = 0 if index_x == 0 else index_x - 1
        upper_x = size_x - 1 if index_x == size_x - 1 else index_x + 1
        lower_y = 0 if index_y == 0 else index_y - 1
        upper_y = size_y - 1 if index_y == size_y - 1 else index_y + 1

        activity_value = activity[index_x, index_y]
        heat_value = heat[index_x, index_y]
        wave_value = wave[index_x, index_y]
        velocity_value = wave_velocity[index_x, index_y]

        activity_laplacian = (
            activity[lower_x, index_y]
            - 2.0 * activity_value
            + activity[upper_x, index_y]
        ) * inverse_dx_squared + (
            activity[index_x, lower_y]
            - 2.0 * activity_value
            + activity[index_x, upper_y]
        ) * inverse_dy_squared
        heat_laplacian = (
            heat[lower_x, index_y]
            - 2.0 * heat_value
            + heat[upper_x, index_y]
        ) * inverse_dx_squared + (
            heat[index_x, lower_y]
            - 2.0 * heat_value
            + heat[index_x, upper_y]
        ) * inverse_dy_squared
        wave_laplacian = (
            wave[lower_x, index_y]
            - 2.0 * wave_value
            + wave[upper_x, index_y]
        ) * inverse_dx_squared + (
            wave[index_x, lower_y]
            - 2.0 * wave_value
            + wave[index_x, upper_y]
        ) * inverse_dy_squared

        saturation = max(1.0 - activity_value, 0.0)
        activity_rate = (
            activity_diffusivity * activity_laplacian
            + local_growth[index_x, index_y] * activity_value * saturation
            + heat_feedback * heat_value * saturation
            - local_loss[index_x, index_y] * activity_value
        )
        heat_rate = (
            heat_diffusivity * heat_laplacian
            + heat_source_rate * activity_value
            - heat_decay_rate * heat_value
        )
        wave_velocity_rate = (
            wave_speed_squared * wave_laplacian
            + wave_source_rate * activity_value
            - wave_damping * velocity_value
        )

        midpoint_activity[index_x, index_y] = min(
            max(activity_value + half_timestep * activity_rate, 0.0),
            1.0,
        )
        midpoint_heat[index_x, index_y] = max(
            heat_value + half_timestep * heat_rate,
            0.0,
        )
        midpoint_wave[index_x, index_y] = (
            wave_value + half_timestep * velocity_value
        )
        midpoint_wave_velocity[index_x, index_y] = (
            velocity_value + half_timestep * wave_velocity_rate
        )
    ####

    for flat_index in prange(cell_count):
        index_x = flat_index // size_y
        index_y = flat_index - index_x * size_y

        lower_x = 0 if index_x == 0 else index_x - 1
        upper_x = size_x - 1 if index_x == size_x - 1 else index_x + 1
        lower_y = 0 if index_y == 0 else index_y - 1
        upper_y = size_y - 1 if index_y == size_y - 1 else index_y + 1

        activity_value = midpoint_activity[index_x, index_y]
        heat_value = midpoint_heat[index_x, index_y]
        wave_value = midpoint_wave[index_x, index_y]
        velocity_value = midpoint_wave_velocity[index_x, index_y]

        activity_laplacian = (
            midpoint_activity[lower_x, index_y]
            - 2.0 * activity_value
            + midpoint_activity[upper_x, index_y]
        ) * inverse_dx_squared + (
            midpoint_activity[index_x, lower_y]
            - 2.0 * activity_value
            + midpoint_activity[index_x, upper_y]
        ) * inverse_dy_squared
        heat_laplacian = (
            midpoint_heat[lower_x, index_y]
            - 2.0 * heat_value
            + midpoint_heat[upper_x, index_y]
        ) * inverse_dx_squared + (
            midpoint_heat[index_x, lower_y]
            - 2.0 * heat_value
            + midpoint_heat[index_x, upper_y]
        ) * inverse_dy_squared
        wave_laplacian = (
            midpoint_wave[lower_x, index_y]
            - 2.0 * wave_value
            + midpoint_wave[upper_x, index_y]
        ) * inverse_dx_squared + (
            midpoint_wave[index_x, lower_y]
            - 2.0 * wave_value
            + midpoint_wave[index_x, upper_y]
        ) * inverse_dy_squared

        saturation = max(1.0 - activity_value, 0.0)
        activity_rate = (
            activity_diffusivity * activity_laplacian
            + local_growth[index_x, index_y] * activity_value * saturation
            + heat_feedback * heat_value * saturation
            - local_loss[index_x, index_y] * activity_value
        )
        heat_rate = (
            heat_diffusivity * heat_laplacian
            + heat_source_rate * activity_value
            - heat_decay_rate * heat_value
        )
        wave_velocity_rate = (
            wave_speed_squared * wave_laplacian
            + wave_source_rate * activity_value
            - wave_damping * velocity_value
        )

        activity[index_x, index_y] = min(
            max(
                activity[index_x, index_y] + timestep * activity_rate,
                0.0,
            ),
            1.0,
        )
        heat[index_x, index_y] = max(
            heat[index_x, index_y] + timestep * heat_rate,
            0.0,
        )
        wave[index_x, index_y] += timestep * velocity_value
        wave_velocity[index_x, index_y] += timestep * wave_velocity_rate
    ####
####


@njit(cache=True, fastmath=True, parallel=True)
def _advance_3d(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    wave_velocity: FloatArray,
    local_growth: FloatArray,
    local_loss: FloatArray,
    activity_diffusivity: float,
    heat_diffusivity: float,
    heat_feedback: float,
    heat_source_rate: float,
    heat_decay_rate: float,
    wave_speed_squared: float,
    wave_source_rate: float,
    wave_damping: float,
    inverse_dx_squared: float,
    inverse_dy_squared: float,
    inverse_dz_squared: float,
    timestep: float,
    midpoint_activity: FloatArray,
    midpoint_heat: FloatArray,
    midpoint_wave: FloatArray,
    midpoint_wave_velocity: FloatArray,
) -> None:
    size_x, size_y, size_z = activity.shape
    yz_size = size_y * size_z
    cell_count = size_x * yz_size
    half_timestep = 0.5 * timestep

    for flat_index in prange(cell_count):
        index_x = flat_index // yz_size
        remainder = flat_index - index_x * yz_size
        index_y = remainder // size_z
        index_z = remainder - index_y * size_z

        lower_x = 0 if index_x == 0 else index_x - 1
        upper_x = size_x - 1 if index_x == size_x - 1 else index_x + 1
        lower_y = 0 if index_y == 0 else index_y - 1
        upper_y = size_y - 1 if index_y == size_y - 1 else index_y + 1
        lower_z = 0 if index_z == 0 else index_z - 1
        upper_z = size_z - 1 if index_z == size_z - 1 else index_z + 1

        activity_value = activity[index_x, index_y, index_z]
        heat_value = heat[index_x, index_y, index_z]
        wave_value = wave[index_x, index_y, index_z]
        velocity_value = wave_velocity[index_x, index_y, index_z]

        activity_laplacian = (
            activity[lower_x, index_y, index_z]
            - 2.0 * activity_value
            + activity[upper_x, index_y, index_z]
        ) * inverse_dx_squared + (
            activity[index_x, lower_y, index_z]
            - 2.0 * activity_value
            + activity[index_x, upper_y, index_z]
        ) * inverse_dy_squared + (
            activity[index_x, index_y, lower_z]
            - 2.0 * activity_value
            + activity[index_x, index_y, upper_z]
        ) * inverse_dz_squared
        heat_laplacian = (
            heat[lower_x, index_y, index_z]
            - 2.0 * heat_value
            + heat[upper_x, index_y, index_z]
        ) * inverse_dx_squared + (
            heat[index_x, lower_y, index_z]
            - 2.0 * heat_value
            + heat[index_x, upper_y, index_z]
        ) * inverse_dy_squared + (
            heat[index_x, index_y, lower_z]
            - 2.0 * heat_value
            + heat[index_x, index_y, upper_z]
        ) * inverse_dz_squared
        wave_laplacian = (
            wave[lower_x, index_y, index_z]
            - 2.0 * wave_value
            + wave[upper_x, index_y, index_z]
        ) * inverse_dx_squared + (
            wave[index_x, lower_y, index_z]
            - 2.0 * wave_value
            + wave[index_x, upper_y, index_z]
        ) * inverse_dy_squared + (
            wave[index_x, index_y, lower_z]
            - 2.0 * wave_value
            + wave[index_x, index_y, upper_z]
        ) * inverse_dz_squared

        saturation = max(1.0 - activity_value, 0.0)
        activity_rate = (
            activity_diffusivity * activity_laplacian
            + local_growth[index_x, index_y, index_z]
            * activity_value
            * saturation
            + heat_feedback * heat_value * saturation
            - local_loss[index_x, index_y, index_z] * activity_value
        )
        heat_rate = (
            heat_diffusivity * heat_laplacian
            + heat_source_rate * activity_value
            - heat_decay_rate * heat_value
        )
        wave_velocity_rate = (
            wave_speed_squared * wave_laplacian
            + wave_source_rate * activity_value
            - wave_damping * velocity_value
        )

        midpoint_activity[index_x, index_y, index_z] = min(
            max(activity_value + half_timestep * activity_rate, 0.0),
            1.0,
        )
        midpoint_heat[index_x, index_y, index_z] = max(
            heat_value + half_timestep * heat_rate,
            0.0,
        )
        midpoint_wave[index_x, index_y, index_z] = (
            wave_value + half_timestep * velocity_value
        )
        midpoint_wave_velocity[index_x, index_y, index_z] = (
            velocity_value + half_timestep * wave_velocity_rate
        )
    ####

    for flat_index in prange(cell_count):
        index_x = flat_index // yz_size
        remainder = flat_index - index_x * yz_size
        index_y = remainder // size_z
        index_z = remainder - index_y * size_z

        lower_x = 0 if index_x == 0 else index_x - 1
        upper_x = size_x - 1 if index_x == size_x - 1 else index_x + 1
        lower_y = 0 if index_y == 0 else index_y - 1
        upper_y = size_y - 1 if index_y == size_y - 1 else index_y + 1
        lower_z = 0 if index_z == 0 else index_z - 1
        upper_z = size_z - 1 if index_z == size_z - 1 else index_z + 1

        activity_value = midpoint_activity[index_x, index_y, index_z]
        heat_value = midpoint_heat[index_x, index_y, index_z]
        wave_value = midpoint_wave[index_x, index_y, index_z]
        velocity_value = midpoint_wave_velocity[index_x, index_y, index_z]

        activity_laplacian = (
            midpoint_activity[lower_x, index_y, index_z]
            - 2.0 * activity_value
            + midpoint_activity[upper_x, index_y, index_z]
        ) * inverse_dx_squared + (
            midpoint_activity[index_x, lower_y, index_z]
            - 2.0 * activity_value
            + midpoint_activity[index_x, upper_y, index_z]
        ) * inverse_dy_squared + (
            midpoint_activity[index_x, index_y, lower_z]
            - 2.0 * activity_value
            + midpoint_activity[index_x, index_y, upper_z]
        ) * inverse_dz_squared
        heat_laplacian = (
            midpoint_heat[lower_x, index_y, index_z]
            - 2.0 * heat_value
            + midpoint_heat[upper_x, index_y, index_z]
        ) * inverse_dx_squared + (
            midpoint_heat[index_x, lower_y, index_z]
            - 2.0 * heat_value
            + midpoint_heat[index_x, upper_y, index_z]
        ) * inverse_dy_squared + (
            midpoint_heat[index_x, index_y, lower_z]
            - 2.0 * heat_value
            + midpoint_heat[index_x, index_y, upper_z]
        ) * inverse_dz_squared
        wave_laplacian = (
            midpoint_wave[lower_x, index_y, index_z]
            - 2.0 * wave_value
            + midpoint_wave[upper_x, index_y, index_z]
        ) * inverse_dx_squared + (
            midpoint_wave[index_x, lower_y, index_z]
            - 2.0 * wave_value
            + midpoint_wave[index_x, upper_y, index_z]
        ) * inverse_dy_squared + (
            midpoint_wave[index_x, index_y, lower_z]
            - 2.0 * wave_value
            + midpoint_wave[index_x, index_y, upper_z]
        ) * inverse_dz_squared

        saturation = max(1.0 - activity_value, 0.0)
        activity_rate = (
            activity_diffusivity * activity_laplacian
            + local_growth[index_x, index_y, index_z]
            * activity_value
            * saturation
            + heat_feedback * heat_value * saturation
            - local_loss[index_x, index_y, index_z] * activity_value
        )
        heat_rate = (
            heat_diffusivity * heat_laplacian
            + heat_source_rate * activity_value
            - heat_decay_rate * heat_value
        )
        wave_velocity_rate = (
            wave_speed_squared * wave_laplacian
            + wave_source_rate * activity_value
            - wave_damping * velocity_value
        )

        activity[index_x, index_y, index_z] = min(
            max(
                activity[index_x, index_y, index_z]
                + timestep * activity_rate,
                0.0,
            ),
            1.0,
        )
        heat[index_x, index_y, index_z] = max(
            heat[index_x, index_y, index_z] + timestep * heat_rate,
            0.0,
        )
        wave[index_x, index_y, index_z] += timestep * velocity_value
        wave_velocity[index_x, index_y, index_z] += (
            timestep * wave_velocity_rate
        )
    ####
####


@dataclass(slots=True)
class NumbaReactionStepper:
    """Fused midpoint stepper compiled by Numba for repeated grid updates."""

    config: ReactionDiffusionConfig
    local_growth: FloatArray
    local_loss: FloatArray
    midpoint_activity: FloatArray
    midpoint_heat: FloatArray
    midpoint_wave: FloatArray
    midpoint_wave_velocity: FloatArray
    inverse_spacing_squared: tuple[float, ...]

    @classmethod
    def create(
        cls,
        config: ReactionDiffusionConfig,
        activity: FloatArray,
        catalyst: FloatArray,
        quencher: FloatArray,
    ) -> NumbaReactionStepper:
        local_growth = config.base_growth_rate * (
            1.0 + config.catalyst_gain * catalyst
        )
        local_loss = config.base_loss_rate + config.quencher_strength * quencher
        return cls(
            config=config,
            local_growth=local_growth,
            local_loss=local_loss,
            midpoint_activity=np.empty_like(activity),
            midpoint_heat=np.empty_like(activity),
            midpoint_wave=np.empty_like(activity),
            midpoint_wave_velocity=np.empty_like(activity),
            inverse_spacing_squared=tuple(
                1.0 / (spacing * spacing) for spacing in config.spacing
            ),
        )
    ####

    def step(
        self,
        activity: FloatArray,
        heat: FloatArray,
        wave: FloatArray,
        wave_velocity: FloatArray,
        timestep: float,
    ) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
        config = self.config
        inverse_spacing_squared = self.inverse_spacing_squared
        common_arguments = (
            activity,
            heat,
            wave,
            wave_velocity,
            self.local_growth,
            self.local_loss,
            config.activity_diffusivity,
            config.heat_diffusivity,
            config.heat_feedback,
            config.heat_source_rate,
            config.heat_decay_rate,
            config.wave_speed * config.wave_speed,
            config.wave_source_rate,
            config.wave_damping,
        )

        if config.dimensions == 1:
            _advance_1d(
                *common_arguments,
                inverse_spacing_squared[0],
                timestep,
                self.midpoint_activity,
                self.midpoint_heat,
                self.midpoint_wave,
                self.midpoint_wave_velocity,
            )
        elif config.dimensions == 2:
            _advance_2d(
                *common_arguments,
                inverse_spacing_squared[0],
                inverse_spacing_squared[1],
                timestep,
                self.midpoint_activity,
                self.midpoint_heat,
                self.midpoint_wave,
                self.midpoint_wave_velocity,
            )
        else:
            _advance_3d(
                *common_arguments,
                inverse_spacing_squared[0],
                inverse_spacing_squared[1],
                inverse_spacing_squared[2],
                timestep,
                self.midpoint_activity,
                self.midpoint_heat,
                self.midpoint_wave,
                self.midpoint_wave_velocity,
            )
        ####
        return activity, heat, wave, wave_velocity
    ####
####
