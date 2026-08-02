from pathlib import Path
import sys

import numpy as np


REGISTRATION_DIR = Path(__file__).parents[1] / "notes" / "development" / "point-cloud-registration"
sys.path.insert(0, str(REGISTRATION_DIR))

from metrics import (  # noqa: E402
    chamfer_distance,
    random_special_orthogonal_matrix,
    rmse,
    rmse_nearest,
    rotation_angle_degrees,
)


def test_point_cloud_metrics_have_expected_scales() -> None:
    reference = np.asarray([[0.0, 0.0], [1.0, 0.0]])
    candidate = np.asarray([[0.0, 0.0], [2.0, 0.0]])

    assert rmse(reference, candidate) == np.sqrt(0.5)
    assert rmse_nearest(reference, candidate) == np.sqrt(0.5)
    assert chamfer_distance(reference, candidate) == 1.0


def test_rotation_generator_and_angle() -> None:
    rng = np.random.default_rng(7)
    rotation = random_special_orthogonal_matrix(3, rng=rng)

    assert np.allclose(rotation.T @ rotation, np.eye(3))
    np.testing.assert_allclose(np.linalg.det(rotation), 1.0)
    np.testing.assert_allclose(rotation_angle_degrees(rotation, rotation), 0.0, atol=1e-5)


def test_invalid_point_cloud_inputs_are_rejected() -> None:
    with np.testing.assert_raises(ValueError):
        rmse(np.empty((0, 3)), np.empty((0, 3)))
    with np.testing.assert_raises(ValueError):
        rmse(np.ones((2, 2)), np.ones((3, 2)))
    with np.testing.assert_raises(ValueError):
        rotation_angle_degrees(np.eye(2), np.eye(2))
