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

```sh
uv sync --extra dev
uv run pytest
```

Linux is the development target. GPU work targets an RX 9070 XT under
ROCm on Ubuntu 24.04.

## License

MIT.
