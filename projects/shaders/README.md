# Shader experiments

> Type: collection  
> Status: historical  
> Updated: 2026-08-01

The old shader directory mixed personal experiments, copied or adapted `Shadertoy` examples, and
large scene files. This collection keeps the durable shader source and browser-oriented experiments
while separating reusable code from copied or attributed material.

## What the retained snippet means

Each point scatterer contributes a complex phasor

\[
 a_i e^{i\,\mathbf{k}\cdot\mathbf{x}_i},
\]

represented in GLSL as a two-component real/imaginary vector. Contributions must be summed as
complex values before taking the squared magnitude:

\[
 I = \left|\sum_i a_i e^{i\,\mathbf{k}\cdot\mathbf{x}_i}\right|^2.
\]

The old version declared the accumulator without initializing it. The retained snippet starts it
at `vec2(0.0)` and names the operations explicitly.

This is useful for visualizing phase interference, but it is not by itself a validated radar-cross-
section model. A physical result would also require a defined scattering model, units, coordinate
conventions, polarization, illumination, boundary conditions, and validation against a reference
case. Do not interpret the display as a calibrated measurement.

## Browser preview

The [GLSL shader gallery](shader-gallery/index.html) discovers durable `.glsl` files under
`notes/` and `projects/shaders/` and displays their source. The retained point-scatterer helper
also has a small WebGL2 adapter so its interference pattern can be viewed interactively.
From the repository root, start the local server:

```
uv run python scripts/serve_shader_gallery.py
```

Then open the URL printed by the server. A future shader appears in the source list automatically;
it needs an explicit adapter before the gallery will render it.
The server only serves the gallery assets, linked project notes, and `.glsl`
files under `notes/` or `projects/shaders/`. Hidden, ignored, symlinked and
hard-linked paths are excluded, and directory listings are disabled.
Serving files requires Python to support descriptor-relative opens with
`O_DIRECTORY`, `O_NOFOLLOW`, and `O_NONBLOCK`; without those capabilities the
server fails closed and will not serve gallery files or shaders. Python's
descriptor-relative opens are unavailable on Windows, so use a supported Unix
environment for this server; a native Windows implementation remains unverified.

Run the collection's focused test from the repository root:

```shell
python -m pytest projects/shaders/tests
```

The historical `python -m pytest tests/test_shader_collection.py` entrypoint remains available.

## Omitted source material

- The large `duck` / surface-temperature shader pair was a duplicated scene experiment; the
  relevant mesh conversion is now covered by the validated mesh-tools OBJ/GLSL helper.
- `journey.glsl`, `blobby.glsl`, and `radiometric.glsl` contain attributed or adapted `Shadertoy`
  material. They remain source references rather than copied third-party programs.
- The remaining ray-marching and lighting helpers were exploratory and had no reproducible test
  harness. They can be revisited as focused snippets if a concrete question emerges.

GLSL compilation is not part of the Python test environment. Keep generated renders and shader
captures under ignored `artifacts/` when experimenting.
