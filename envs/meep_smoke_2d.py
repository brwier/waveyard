"""Smoke test for the waveyard Meep environment.

A 2D straight silicon waveguide: an eigenmode source at one end, a flux
monitor at the other. It proves three things at once -- that pymeep imports,
that ``mp.EigenModeSource`` works (it needs MPB, a separate shared library),
and that flux monitoring works. Those are exactly the two Meep features the
spec's Meep comparisons need (docs/spec/v0.1.md 11.4, tests I2 and I4), so
this file is the seed of that comparison rather than a throwaway.

Run it with::

    conda run -n waveyard-meep python envs/meep_smoke_2d.py

Geometry, in Meep units of 1 um: a 0.5 um wide n = 3.48 core running along x
through an n = 1.444 cladding, in a 10 x 4 um cell with 1 um of PML on every
side, at resolution 20 (pixels per um). Constant indices, not a Lorentz fit,
because that is what I2/I4 specify for the comparison.
"""

import time

import meep as mp

WAVELENGTH = 1.55  # um
CELL_X, CELL_Y = 10.0, 4.0  # um
PML_THICKNESS = 1.0  # um
CORE_WIDTH = 0.5  # um
N_CORE = 3.48  # silicon at 1.55 um
N_CLAD = 1.444  # silica at 1.55 um
RESOLUTION = 20  # pixels per um
SOURCE_X = -3.0  # um
MONITOR_X = 3.0  # um


def main() -> None:
    fcen = 1.0 / WAVELENGTH
    df = 0.2 * fcen

    cell = mp.Vector3(CELL_X, CELL_Y)
    core = mp.Block(
        size=mp.Vector3(mp.inf, CORE_WIDTH, mp.inf),
        center=mp.Vector3(),
        material=mp.Medium(index=N_CORE),
    )

    source = mp.EigenModeSource(
        src=mp.GaussianSource(fcen, fwidth=df),
        center=mp.Vector3(SOURCE_X, 0),
        size=mp.Vector3(0, CELL_Y - 2 * PML_THICKNESS),
        eig_band=1,
        eig_parity=mp.ODD_Z,
        eig_match_freq=True,
    )

    sim = mp.Simulation(
        cell_size=cell,
        resolution=RESOLUTION,
        boundary_layers=[mp.PML(PML_THICKNESS)],
        geometry=[core],
        sources=[source],
        default_material=mp.Medium(index=N_CLAD),
    )

    monitor_point = mp.Vector3(MONITOR_X, 0)
    flux = sim.add_flux(
        fcen,
        0,
        1,
        mp.FluxRegion(
            center=monitor_point,
            size=mp.Vector3(0, CELL_Y - 2 * PML_THICKNESS),
        ),
    )

    started = time.perf_counter()
    sim.run(
        until_after_sources=mp.stop_when_fields_decayed(50, mp.Ez, monitor_point, 1e-3)
    )
    elapsed = time.perf_counter() - started

    transmitted = mp.get_fluxes(flux)[0]
    print(f"flux at {WAVELENGTH} um: {transmitted:.6g}")
    print(f"meep version: {mp.__version__}")
    print(f"wall time: {elapsed:.2f} s")


if __name__ == "__main__":
    main()
