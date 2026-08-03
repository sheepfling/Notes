from __future__ import annotations

import numpy as np
import pytest

from converging_flow.backend import get_array_backend


def test_cupy_backend_round_trip_when_cuda_is_available() -> None:
    try:
        backend = get_array_backend("cupy")
    except RuntimeError as error:
        pytest.skip(str(error))

    values = np.arange(12, dtype=np.float64).reshape(3, 4)
    device_values = backend.asarray(values)

    assert backend.name == "cupy"
    assert np.array_equal(backend.to_numpy(device_values), values)
    backend.synchronize()
