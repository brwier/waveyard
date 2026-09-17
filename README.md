# waveyard

A small, understandable electromagnetic simulator for photonic integrated
circuits. FDTD on a Yee grid, from GDS layout to S-parameters, written to
learn how such software is structured, one layer at a time.

**Status:** planning. The specification is being re-cut from
[`docs/spec/v0.1.md`](docs/spec/v0.1.md) into a learning-first v0.2; the
route there is charted as a wayfinder map on this repo's issues
(label `wayfinder:map`).

## Why

Two purposes, equally weighted:

1. Rebuild and modernise the author's programming skills by writing the
   numerical core and the architecture by hand.
2. Learn, and write down, the underlying structure of a field simulator:
   why the object model, the discretisation plan, and the compute backends
   are separate layers, and how one functional stepper runs on NumPy and
   PyTorch alike.

Validation against analytic cases and against Meep stays a first-class goal,
because it is how you know the code is right.

## Planned shape (from the v0.1 spec)

- Declarative object model (pydantic) → discretisation `Plan` → backend.
- 3D Yee FDTD with 2D as the degenerate case, CPML, Lorentz ADE media,
  eigenmode sources, DFT mode monitors.
- Full-vector finite-difference mode solver.
- gdsfactory layouts in, S-parameters (xarray, Touchstone, sax) out.
- Backends: NumPy (reference), PyTorch (CPU, ROCm); wgpu later.

## Development

Python 3.12 via [`uv`](https://docs.astral.sh/uv/). From a fresh clone
(commands from `docs/research/python-deps.md`; note `uv sync` is exact, so
name every extra you want in one call):

```sh
uv venv --python 3.12
uv sync --extra core --extra gds --extra wgpu --extra dev
uv sync --extra torch          # pulls torch==2.14.0+cpu via the pinned index above
```

The everyday loop is what CI runs: `uv sync --extra core --extra dev`, then
`uv run ruff check .`, `uv run mypy src`, `uv run pytest -m unit`.

The desktop installs torch from the ROCm index with `uv pip install torch
--index-url https://download.pytorch.org/whl/rocm7.2` after every `uv sync`,
because `uv sync` prunes anything that is not in the lockfile.

Linux is the development target. GPU work targets an RX 9070 XT under
ROCm 7.2 on Ubuntu 24.04.

## License

MIT.
