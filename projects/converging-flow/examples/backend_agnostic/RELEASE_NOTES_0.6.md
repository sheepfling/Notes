# Version 0.6.0: backend-neutral arrays, implicit diffusion, and reactive Euler coupling

## Added

- `ArrayBackend` with `auto`, `numpy`, and optional `cupy` selection.
- Backend-neutral conservative Euler flux implementation.
- Matrix-free variable-coefficient Crank–Nicolson diffusion.
- SciPy GMRES on CPU and CuPy GMRES on GPU through one operator contract.
- Jacobi preconditioning derived from harmonic face coefficients.
- Strang splitting between local/wave dynamics and diffusion.
- Automatic explicit-versus-implicit diffusion selection.
- Backend-neutral reactive Euler state with transported reaction progress.
- Energy-release source coupling that raises EOS pressure.
- Optional independently modeled force-density coupling with consistent work.
- A normalized reactive-pressure demonstration and CPU benchmark artifacts.

## Corrected physical interpretation

A reactive gas normally does not receive an arbitrary directional “reaction pressure” body
force. Reaction progress releases internal energy; the equation of state converts that
energy into pressure; the Euler pressure flux accelerates the material. A separate momentum
source belongs only to an independently modeled force or mass/momentum injection process.

## Validation executed here

- 46 pytest tests passed.
- Source and tests compiled successfully.
- NumPy explicit and Crank–Nicolson runs completed.
- Automatic diffusion selection exercised both branches.
- Automatic backend selection fell back to NumPy without CuPy.
- Inert Euler and RWAS installed-wheel CLI smoke tests passed.
- Installed-wheel reactive Euler source smoke test passed.

## Environment limitation

This environment did not contain CuPy or a usable CUDA device. The GPU path is implemented
against CuPy-compatible array and sparse-linear-algebra interfaces, but must be executed on
the target RTX 5080 system before GPU numerical parity or performance is claimed.
