import numpy as np

from notes.development.vector_geometry.orthogonal_vector import orthonormal_to


def test_orthonormal_to_is_perpendicular_and_unit_length() -> None:
    value = np.array([1.0, 2.0, 3.0])
    result = orthonormal_to(value)

    assert np.isclose(np.dot(value, result), 0.0)
    assert np.isclose(np.linalg.norm(result), 1.0)


def test_orthonormal_to_rejects_invalid_inputs() -> None:
    for value in (np.zeros(3), np.ones(1), np.ones((2, 2))):
        try:
            orthonormal_to(value)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid vector was accepted")
