"""Throwaway prototype for ticket #7: the smallest three-layer 1D FDTD.

Three layers, in order: an object model (physical-ish description), a
discretisation plan (plain arrays; the whole backend contract), and a
backend (frozen State + pure step).  Run it with

    uv run python prototypes/three_layer_1d.py

Physics from John B. Schneider, *Understanding the FDTD Method* (CC BY-SA).
Equation numbers cited inline are his.  This is not milestone-one code.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import matplotlib
import numpy as np

matplotlib.use("Agg")  # headless: the PNG must render with no display

from matplotlib import pyplot as plt

# ---------------------------------------------------------------------------
# LAYER 1 - OBJECT MODEL.  Physical-ish description of the problem.
# No arrays, no cell indices, no coefficients.  Lengths are in micrometres.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Simulation:
    """What the user means.  Nothing here knows about the grid."""

    length_um: float = 40.0  # domain length
    resolution: float = 20.0  # cells per micrometre
    source_pos_um: float = 10.0  # additive soft source position
    pulse_width_um: float = 0.75  # Gaussian 1/e half-width, as a length
    pulse_delay_um: float = 3.0  # turn-on delay, as a length
    monitor_pos_um: float = 20.0  # time-monitor position
    absorber_um: float = 1.0  # graded lossy layer thickness, each end
    run_um: float = 85.0  # run "time", as the distance light travels
    courant: float = 1.0  # Sc = c*dt/dx; 1.0 is the 1D magic time step
    absorber_order: float = 3.0  # polynomial grading exponent
    absorber_loss_max: float = 0.45  # peak of sigma*dt/(2*eps) at the wall


# ---------------------------------------------------------------------------
# LAYER 2 - PLAN.  Plain NumPy arrays and scalars only.  This is the entire
# contract between physics and backend: nothing downstream computes a
# physical coefficient, looks at a material, or knows what a micrometre is.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Plan:
    """Everything the stepper is allowed to know."""

    ce_a: np.ndarray  # (nx,)   E self-coefficient, loss folded in
    ce_b: np.ndarray  # (nx,)   E curl-of-H coefficient
    ch_a: np.ndarray  # (nx-1,) H self-coefficient, matched magnetic loss
    ch_b: np.ndarray  # (nx-1,) H curl-of-E coefficient
    g: np.ndarray  # (n_steps,) source waveform table g[n]
    src_index: int
    mon_index: int
    n_steps: int
    nx: int
    dx: float
    dt: float
    courant: float
    absorber_cells: int  # kept for plotting only; the stepper ignores it


def _graded_loss(positions: np.ndarray, plan_nx: int, npml: int, sim: Simulation):
    """Polynomial-graded loss parameter L = sigma*dt/(2*eps), dimensionless.

    Schneider Sec. 11.2 notes a 1D lossy layer is reflectionless when the
    electric and magnetic losses are matched, sigma_m/mu = sigma/eps
    (Eq. 11.21), which makes eta_2 = eta_1 (Eq. 11.22) and hence Gamma = 0
    (Eq. 11.20) at every frequency; and that the conductivity should be
    raised gradually through the layer to keep the discrete grid from seeing
    a step.  Grading it as a polynomial in depth is the standard choice.
    """
    depth_left = (npml - positions) / npml
    depth_right = (positions - (plan_nx - 1 - npml)) / npml
    depth = np.clip(np.maximum(depth_left, depth_right), 0.0, 1.0)
    return sim.absorber_loss_max * depth**sim.absorber_order


def discretize(sim: Simulation) -> Plan:
    """Layer 1 -> Layer 2.  The only place physics becomes numbers."""
    dx = 1.0 / sim.resolution
    nx = round(sim.length_um * sim.resolution)
    dt = sim.courant * dx  # in units where c = 1
    n_steps = round(sim.run_um / (sim.courant * dx))
    npml = max(1, round(sim.absorber_um * sim.resolution))

    # Loss sampled at the E nodes (integer m) and at the H nodes (m + 1/2).
    loss_e = _graded_loss(np.arange(nx, dtype=np.float64), nx, npml, sim)
    loss_h = _graded_loss(np.arange(nx - 1, dtype=np.float64) + 0.5, nx, npml, sim)

    # Lossy update coefficients.  Schneider Eq. (3.52) for E (semi-implicit
    # time average of Ez, Eq. 3.50) and Eq. (3.56) for H; both reduce to the
    # lossless Eq. (3.18) / Eq. (3.15) where L = 0.  Fields are normalised
    # (E~ = sqrt(eps0/mu0) E) so the lossless coefficient is just Sc.
    ce_a = (1.0 - loss_e) / (1.0 + loss_e)
    ce_b = sim.courant / (1.0 + loss_e)
    ch_a = (1.0 - loss_h) / (1.0 + loss_h)
    ch_b = sim.courant / (1.0 + loss_h)
    ce_a[0] = ce_a[-1] = 0.0  # PEC walls behind the absorber
    ce_b[0] = ce_b[-1] = 0.0

    # Gaussian pulse, Schneider Sec. 5.2.1: g[n] = exp(-((n - n0)/n_w)^2).
    n = np.arange(n_steps, dtype=np.float64)
    n0 = sim.pulse_delay_um / (sim.courant * dx)
    nw = sim.pulse_width_um / (sim.courant * dx)
    g = np.exp(-(((n - n0) / nw) ** 2))

    return Plan(
        ce_a=ce_a,
        ce_b=ce_b,
        ch_a=ch_a,
        ch_b=ch_b,
        g=g,
        src_index=round(sim.source_pos_um * sim.resolution),
        mon_index=round(sim.monitor_pos_um * sim.resolution),
        n_steps=n_steps,
        nx=nx,
        dx=dx,
        dt=dt,
        courant=sim.courant,
        absorber_cells=npml,
    )


# ---------------------------------------------------------------------------
# LAYER 3 - BACKEND.  Frozen State, pure step, dumb loop.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class State:
    """Every mutable thing in the simulation, in one frozen object."""

    e: np.ndarray  # (nx,)
    h: np.ndarray  # (nx-1,)
    tm: np.ndarray  # (n_steps,) time-monitor buffer
    n: int


def init(plan: Plan) -> State:
    return State(
        e=np.zeros(plan.nx),
        h=np.zeros(plan.nx - 1),
        tm=np.zeros(plan.n_steps),
        n=0,
    )


def step(state: State, plan: Plan, n: int) -> State:
    """Pure: allocates new arrays, never mutates its inputs.

    Order follows spec v0.1 Sec. 8.4: update_h -> update_e -> inject_J ->
    record_time.  The Yee leapfrog itself is Schneider Fig. 3.1 / Fig. 3.2,
    Eq. (3.15) and Eq. (3.18), with loss from Eq. (3.56) and Eq. (3.52).
    """
    # --- H update (t = n + 1/2), uses E^n ---
    h = plan.ch_a * state.h + plan.ch_b * (state.e[1:] - state.e[:-1])

    # --- E update (t = n + 1), uses H^{n+1/2} ---
    e = state.e.copy()
    e[1:-1] = plan.ce_a[1:-1] * state.e[1:-1] + plan.ce_b[1:-1] * (h[1:] - h[:-1])
    e[0] = 0.0
    e[-1] = 0.0

    # --- additive soft source (Schneider Sec. 3.8) ---
    e[plan.src_index] += plan.g[n]

    # --- monitors accumulate into state; no side effects, no callbacks ---
    tm = state.tm.copy()
    tm[n] = e[plan.mon_index]

    return State(e=e, h=h, tm=tm, n=n + 1)


def run(plan: Plan, snapshot_at: tuple[int, ...] = ()) -> tuple[State, dict]:
    """The loop is backend-specific; only `step` has to stay pure."""
    state = init(plan)
    snaps: dict[int, np.ndarray] = {}
    for n in range(plan.n_steps):
        state = step(state, plan, n)
        if n in snapshot_at:
            snaps[n] = state.e  # already a fresh array; no copy needed
    return state, snaps


def run_in_place(plan: Plan) -> State:
    """Identical math, mutating three preallocated buffers.  The control."""
    e = np.zeros(plan.nx)
    h = np.zeros(plan.nx - 1)
    tm = np.zeros(plan.n_steps)
    for n in range(plan.n_steps):
        h *= plan.ch_a
        h += plan.ch_b * (e[1:] - e[:-1])
        e[1:-1] *= plan.ce_a[1:-1]
        e[1:-1] += plan.ce_b[1:-1] * (h[1:] - h[:-1])
        e[0] = 0.0
        e[-1] = 0.0
        e[plan.src_index] += plan.g[n]
        tm[n] = e[plan.mon_index]
    return State(e=e, h=h, tm=tm, n=plan.n_steps)


# ---------------------------------------------------------------------------
# Driver: reflection figure of merit, benchmark, picture.
# ---------------------------------------------------------------------------


def main() -> None:
    t_wall = time.perf_counter()
    sim = Simulation()
    plan = discretize(sim)

    # The direct pulse passes the monitor once; everything later is a return
    # from one of the two absorbers.  Sc = 1 means one cell per step.
    n_direct = int(plan.g.argmax()) + abs(plan.mon_index - plan.src_index)
    n_split = n_direct + int(4 * sim.pulse_width_um / (sim.courant * plan.dx))
    snapshot_at = (n_direct, n_direct + 330, n_direct + 385, n_direct + 415)

    state, snaps = run(plan, snapshot_at=snapshot_at)
    incident = float(np.abs(state.tm[:n_split]).max())
    returned = float(np.abs(state.tm[n_split:]).max())
    print(f"grid: {plan.nx} cells, {plan.n_steps} steps, Sc = {plan.courant}")
    print(f"absorber: {plan.absorber_cells} cells each end, order {sim.absorber_order}")
    print(f"reflection ratio: {returned / incident:.3e}")

    # Benchmark: fresh arrays every step vs. the same math in place.
    t0 = time.perf_counter()
    run(plan)
    t_func = time.perf_counter() - t0
    t0 = time.perf_counter()
    check = run_in_place(plan)
    t_inplace = time.perf_counter() - t0
    assert np.allclose(check.tm, state.tm), "in-place variant is not the same math"
    print(f"functional: {plan.n_steps / t_func:,.0f} steps/s")
    print(f"in-place: {plan.n_steps / t_inplace:,.0f} steps/s")
    print(f"ratio: {t_func / t_inplace:.2f}")

    # Picture: snapshots of E(x) with the absorber shaded, plus the monitor.
    x = np.arange(plan.nx) * plan.dx
    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(9, 6.5), constrained_layout=True)
    for edge in (0.0, x[-1] - sim.absorber_um):
        ax0.axvspan(edge, edge + sim.absorber_um, color="0.85", zorder=0)
    for n in snapshot_at:
        ax0.plot(x, snaps[n], lw=1.2, label=f"step {n}")
    ax0.axvline(plan.mon_index * plan.dx, color="k", ls=":", lw=0.8)
    ax0.set(xlabel="x (um)", ylabel="Ez (normalised)")
    ax0.set_title("pulse hitting the graded lossy absorber")
    ax0.legend(fontsize=8, ncol=4)

    ax1.semilogy(np.arange(plan.n_steps), np.abs(state.tm) + 1e-16, lw=0.9)
    ax1.axhline(incident, color="0.5", ls="-", lw=0.8, label=f"incident {incident:.2f}")
    ax1.axhline(returned, color="g", ls="-.", lw=0.8, label=f"return {returned:.1e}")
    ax1.axvline(n_split, color="r", ls="--", lw=0.8, label="incident / return split")
    ax1.set(xlabel="step n", ylabel="|Ez| at monitor", ylim=(1e-10, 2.0))
    ax1.set_title(f"time monitor, reflection ratio {returned / incident:.2e}")
    ax1.legend(fontsize=8, ncol=3)
    fig.savefig("prototypes/three_layer_1d.png", dpi=110)
    elapsed = time.perf_counter() - t_wall
    print(f"wrote prototypes/three_layer_1d.png in {elapsed:.2f} s")


if __name__ == "__main__":
    main()
