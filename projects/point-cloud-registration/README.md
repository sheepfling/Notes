# Point-cloud registration scratch lab

> Type: collection  
> Status: needs-review  
> Updated: 2026-08-01

The old PyCPD experiment generated synthetic point clouds, applied scale/rotation/translation,
then compared rigid-registration variants with and without point dropout. Its useful, reusable
part is now isolated in [`metrics.py`](../../src/notes_tools/point_cloud_registration/metrics.py): nearest-neighbor errors, elementwise `RMSE`,
relative 3-D rotation error, and proper-rotation generation.

## Metric meanings

- `rmse` compares corresponding rows using Euclidean point distances and therefore requires equal
  shapes.
- `rmse_nearest` compares each point to its nearest point in the other cloud and can compare
  clouds with different point counts. Its symmetric form averages both directions before taking
  the square root.
- `chamfer_distance` returns the sum of the two mean squared nearest-neighbor distances; it is
  not the same scale as `RMSE`.
- `rotation_angle_degrees` is a 3-D relative-rotation diagnostic. It should not be used on an
  arbitrary affine matrix or on a reflection without checking the input first.

## Optional CPD driver

The original driver used the third-party `pycpd` package and Matplotlib’s interactive 3-D plots.
Those are optional experiment dependencies and are not part of the repository’s default test
path. If recreating that experiment, pin the package versions, use a fixed random seed, save plots
under ignored `artifacts/`, and report whether the comparison uses full or dropped point sets.

The old driver also mixed registration output with truth data and plotting. Keeping metrics
independent makes it easier to test failures such as unequal shapes, empty clouds, non-finite
coordinates, and an estimated matrix that is not a valid 3-D rotation.
