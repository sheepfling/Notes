# Vector geometry snippets

> Type: collection  
> Status: current  
> Updated: 2026-08-01

Small numerical experiments belong here when they have a clear contract and a testable result.

## Constructing an orthogonal unit vector

[orthogonal_vector.py](../../src/notes_tools/vector_geometry/orthogonal_vector.py) returns one deterministic unit vector perpendicular
to a nonzero one-dimensional input. There are infinitely many valid answers in dimensions above
two, so the function chooses the coordinate axis least aligned with the input before removing
the projection and normalizing.

```python
import numpy as np

from notes_tools.vector_geometry.orthogonal_vector import orthonormal_to

v = np.array([1.0, 2.0, 3.0])
w = orthonormal_to(v)
assert np.isclose(np.dot(v, w), 0.0)
assert np.isclose(np.linalg.norm(w), 1.0)
```

The original December snippet attempted to construct an answer by permuting and negating
components. That can be useful for special shapes, but it had ambiguous behavior for scalars,
empty inputs, zero vectors, and higher-dimensional arrays. The replacement states those cases in
the API and raises `ValueError` rather than returning a misleading result.

## Run and test

From the repository root, install the focused dependencies and run:

```shell
python -m pip install -e ".[vector-geometry,testing]"
python -m notes_tools.vector_geometry.orthogonal_vector
python -m pytest tests/test_vector_geometry.py
```

The example prints a vector and its checks; it does not generate files. The
tests stay centralized because they cover the reusable `notes_tools` package.
