# Vector geometry snippets

> Type: collection  
> Status: current  
> Updated: 2026-08-01

Small numerical experiments belong here when they have a clear contract and a testable result.

## Constructing an orthogonal unit vector

[orthogonal_vector.py](orthogonal_vector.py) returns one deterministic unit vector perpendicular
to a nonzero one-dimensional input. There are infinitely many valid answers in dimensions above
two, so the function chooses the coordinate axis least aligned with the input before removing
the projection and normalizing.

```python
import numpy as np

from notes.development.vector_geometry.orthogonal_vector import orthonormal_to

v = np.array([1.0, 2.0, 3.0])
w = orthonormal_to(v)
assert np.isclose(np.dot(v, w), 0.0)
assert np.isclose(np.linalg.norm(w), 1.0)
```

The original December snippet attempted to construct an answer by permuting and negating
components. That can be useful for special shapes, but it had ambiguous behavior for scalars,
empty inputs, zero vectors, and higher-dimensional arrays. The replacement states those cases in
the API and raises `ValueError` rather than returning a misleading result.
