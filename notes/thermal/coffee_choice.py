"""Reproduce the coffee-choice note with a lumped-capacity model.

Adapted from thermal-problems commit d1927b95c5a69b947496c9d55b1a63a94da2bb19,
including its default inputs and Newtonian cooling / energy-weighted mixing.
Python 3.10+; standard library only.
"""

from dataclasses import dataclass
from math import exp


@dataclass(frozen=True)
class Parameters:
    # Temperatures: °C; masses: g; specific heats: J/(g K); conductance: W/K.
    room_c: float = 20.0
    coffee_c: float = 90.0
    creamer_c: float = 5.0
    coffee_g: float = 250.0
    creamer_g: float = 30.0
    coffee_specific_heat: float = 4.18
    creamer_specific_heat: float = 3.90
    conductance_w_per_k: float = 3.0
    total_s: float = 600.0
    add_later_s: float = 300.0
####


def cool(start_c: float, room_c: float, capacity_j_per_k: float,
         conductance_w_per_k: float, seconds: float) -> float:
    """Return the cooled temperature in °C.

    Temperatures are in °C, thermal capacity in J/K, conductance in W/K,
    and elapsed time in seconds. Capacity and conductance remain constant.
    """
    return room_c + (start_c - room_c) * exp(-conductance_w_per_k * seconds / capacity_j_per_k)
####


def mix(coffee_c: float, creamer_c: float, coffee_capacity: float,
        creamer_capacity: float) -> float:
    """Return the ideal instantaneous mixture temperature in °C.

    Input temperatures are in °C and both thermal capacities are in J/K.
    """
    return (coffee_capacity * coffee_c + creamer_capacity * creamer_c) / (coffee_capacity + creamer_capacity)
####


def compare(p: Parameters) -> tuple[float, float]:
    """Return final temperatures in °C, as (creamer now, creamer later)."""
    if (p.coffee_g <= 0 or p.creamer_g <= 0 or p.coffee_specific_heat <= 0
            or p.creamer_specific_heat <= 0 or p.conductance_w_per_k <= 0
            or p.total_s <= 0 or not 0 <= p.add_later_s <= p.total_s):
        raise ValueError("capacities, conductance and duration must be positive; addition must fall within the wait")
    ####
    coffee_capacity = p.coffee_g * p.coffee_specific_heat
    creamer_capacity = p.creamer_g * p.creamer_specific_heat
    mixture_capacity = coffee_capacity + creamer_capacity
    early_mix = mix(p.coffee_c, p.creamer_c, coffee_capacity, creamer_capacity)
    early = cool(early_mix, p.room_c, mixture_capacity, p.conductance_w_per_k, p.total_s)
    before_late_mix = cool(p.coffee_c, p.room_c, coffee_capacity, p.conductance_w_per_k, p.add_later_s)
    late_mix = mix(before_late_mix, p.creamer_c, coffee_capacity, creamer_capacity)
    late = cool(late_mix, p.room_c, mixture_capacity, p.conductance_w_per_k, p.total_s - p.add_later_s)
    return early, late
####


def main() -> None:
    for label, params in (("Cold creamer (5 °C)", Parameters()),
                          ("Warm creamer (70 °C)", Parameters(creamer_c=70.0))):
        early, late = compare(params)
        print(f"{label}: now {early:.2f} °C; later {late:.2f} °C; later minus now {late - early:+.2f} °C")
    ####
####


if __name__ == "__main__":
    main()
####
