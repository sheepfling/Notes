# Should You Add Creamer Now or Later?

> Type: reference
> Status: current
> Updated: 2026-10-29
> Tags: coffee, thermal

You have a hot cup of coffee and ten minutes before you want to drink it.
There are two options:

1. Add cold creamer now and let the drink sit.
2. Let the coffee sit for five minutes, add the creamer, and wait another five.

Which cup is hotter at the end?

The intuitive answer is not quite enough here. Adding the creamer now cools the
coffee immediately, but it also adds thermal mass. Waiting keeps the coffee
hotter for the first five minutes, but then the creamer causes a sharper drop.
The only reliable way to compare those effects is to write down a model.

## A deliberately small model

The simulation makes three simplifying assumptions:

- The coffee and the final coffee-creamer mixture follow Newtonian cooling.
- Mixing is instantaneous and perfectly uniform.
- The cup's effective heat-transfer conductance stays the same after the
  creamer is added.

For a body with temperature \(T\), room temperature \(T_r\), thermal capacity
\(C\), and effective conductance \(G\), the temperature after time \(t\) is

```text
T(t) = T_r + (T_0 - T_r) exp(-G t / C)
```

When the creamer is added, the two contents are mixed using conservation of
energy:

```text
T_mix = (C_coffee T_coffee + C_creamer T_creamer)
        / (C_coffee + C_creamer)
```

The model then cools the mixture for however much time remains.

## The result

Using these assumptions:

- coffee: 250 g at 90 °C
- creamer: 30 g at 5 °C
- room: 20 °C
- total wait: 10 minutes
- late addition: after 5 minutes
- effective conductance: 3.0 W/K
- coffee specific heat: 4.18 J/(g·K), giving 1045 J/K
- creamer specific heat: 3.90 J/(g·K), giving 117 J/K
- mixture capacity: 1162 J/K

the final temperatures are:

| Strategy | Final temperature |
| --- | ---: |
| Creamer now | 33.05 °C |
| Creamer later | 31.57 °C |

Under these assumptions, adding the creamer immediately wins by about **1.49
°C**.

The early-addition cup starts lower because the cold creamer is already mixed
in. But the larger combined thermal capacity slows its subsequent cooling. In
the late-addition case, the coffee has cooled for five minutes on its own; the
creamer then drops it from about 49.58 °C to 45.10 °C before the final cooling
period.

## This is not a universal coffee rule

The creamer remains at its stated temperature until it is added. The model
omits the cup's heat capacity and treats heat loss as a constant effective
conductance; it does not separately model evaporation or radiation.

The conclusion belongs to the model, not to coffee in the abstract. Change the
creamer temperature, the amount of creamer, the cup, or the timing and the
comparison can change. For example, with a warmer 70 °C creamer, the same model
makes the late-addition strategy hotter by about 0.14 °C.

That sensitivity is the useful part of the exercise. A verbal argument tends
to focus on only one effect—either the immediate temperature drop or the later
cooling rate—while the simulation keeps both effects in view.

## Reproduce it

The [small Python proof](coffee_choice.py) uses the original simulation's
cooling and mixing equations and defaults. It was adapted from the local
`thermal-problems` repository at commit
`d1927b95c5a69b947496c9d55b1a63a94da2bb19`; that repository has no configured
remote. The proof needs Python 3.10 or later and only the standard library;
the tests additionally need `pytest`. From the repository root, create a
virtual environment and run:

```shell
python3 -m venv .venv
.venv/bin/python -m pip install pytest
.venv/bin/python -m notes.thermal.coffee_choice
.venv/bin/python -m pytest tests/thermal -v
```

It prints both the default and 70 °C creamer comparisons. The important thing
to preserve when adapting the model is the distinction between cooling before
mixing, instantaneous mixing, and cooling after mixing. The temperatures are
model outputs, not measured coffee temperatures.
