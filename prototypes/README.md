# Three-layer 1D FDTD prototype

Throwaway prototype for ticket #7, on branch `prototype/three-layer-1d`. It
exists to make the three layers of spec v0.1 §8.3–8.4 (object model →
discretisation plan → backend) visible in the smallest case that still has a
source, an absorber and a monitor, so the owner can react to where the
boundaries fall before writing the real thing. Run it with `uv run python
prototypes/three_layer_1d.py` from the repo root (needs the `core` extra);
it takes about 0.7 s wall including the two benchmark runs. It prints the
grid size, the absorber configuration, `reflection ratio:`, and the
`functional:` / `in-place:` / `ratio:` benchmark lines, and writes
`prototypes/three_layer_1d.png` (git-ignored) showing four snapshots of
E(x) with the graded absorber shaded and the time-monitor trace on a log
axis. It is **not** milestone-one code: one file, NumPy and matplotlib only,
no pydantic, no array-api-compat, no tests, and it hard-codes
`prototypes/three_layer_1d.png` as a relative path. The verdicts below are
the owner's; what follows is only what the prototype shows.

Physics is from John B. Schneider, *Understanding the FDTD Method* (CC
BY-SA); equation numbers cited below and in the source are his. The
third-edition Taflove & Hagness chapters the spec cites (§17, ADE media §9,
CPML §7.9) are **not on the desktop yet** — only the 1995 first edition,
which predates CPML and ADE as the spec uses them, so nothing here is
checked against it.

Measured output of the committed script (this machine, one run):

```
grid: 800 cells, 1700 steps, Sc = 1.0
absorber: 20 cells each end, order 3.0
reflection ratio: 1.399e-04
functional: 116,095 steps/s
in-place: 161,254 steps/s
ratio: 1.39
```

## Is the plan really the whole backend contract?

It is in this prototype, and the way you check is that `step()` (line 160)
and `run_in_place()` (line 197) only ever read attributes of `Plan`. Neither
imports `Simulation`, neither mentions a micrometre, a permittivity, a
conductivity or the speed of light. `discretize()` (line 90) is the only
function in the file that does — it is the sole place where physics becomes
numbers.

Every field of `Plan` (lines 55–71), what produces it and what consumes it:

| Field | Shape / type | Produced by | Consumed by |
| --- | --- | --- | --- |
| `ce_a` | `(nx,)` f64 | `discretize` from `absorber_loss_max`, `absorber_order`, `absorber_um`, `resolution` | `step` E update; `run_in_place` |
| `ce_b` | `(nx,)` f64 | same, plus `courant` | `step` E update; `run_in_place` |
| `ch_a` | `(nx-1,)` f64 | same, sampled at half-cells | `step` H update; `run_in_place` |
| `ch_b` | `(nx-1,)` f64 | same, plus `courant` | `step` H update; `run_in_place` |
| `g` | `(n_steps,)` f64 | `discretize` from `pulse_width_um`, `pulse_delay_um` | `step` source injection; the driver, to find the pulse peak |
| `src_index` | `int` | `discretize` from `source_pos_um * resolution` | `step` source injection |
| `mon_index` | `int` | `discretize` from `monitor_pos_um * resolution` | `step` monitor record |
| `n_steps` | `int` | `discretize` from `run_um`, `courant`, `dx` | `run` / `run_in_place` loop bound; `init` buffer size |
| `nx` | `int` | `discretize` from `length_um * resolution` | `init` buffer sizes; the plot |
| `dx` | `float` | `1 / resolution` | reporting and the plot only — no update touches it |
| `dt` | `float` | `courant * dx` | reporting only — no update touches it |
| `courant` | `float` | copied from `Simulation` | already folded into `ce_b` / `ch_b`; kept for reporting |
| `absorber_cells` | `int` | `discretize` | plot shading only; the stepper ignores it (line 71) |

Two observations the table makes concrete. First, the coefficient arrays are
where all the physics went: the PEC end walls are folded in as `ce_a[0] =
ce_a[-1] = 0`, `ce_b[0] = ce_b[-1] = 0` (lines 110–111), exactly the way
spec §8.3 says PEC is folded in as `ca = cb = 0`, and the stepper has no
boundary-condition branch at all. Second, four of the thirteen fields
(`dx`, `dt`, `courant`, `absorber_cells`) are carried but never used by an
update — they are there for reporting and plotting. The prototype does not
say whether that is a leak in the contract or a convenience; it just shows
that the split between "coefficients the stepper uses" and "metadata the
caller wants" already exists at n=13 fields and will not get smaller.

Physics that crossed the boundary and is now invisible downstream: the Yee
leapfrog in 1D (Schneider Fig. 3.1 and Fig. 3.2 for the space-time node
arrangement; Eq. (3.15) for the H update, Eq. (3.18) for the E update), the
lossy versions of both (Eq. (3.52) for E, derived via the time-average
Eq. (3.50), and Eq. (3.56) for H), the Courant number Sc = c·Δt/Δx defined
just after Eq. (3.18) — here Sc = 1.0, the 1D magic time step — and the
Gaussian source table g[n] = exp(−((n − n₀)/n_w)²) of Schneider §5.2.1.

## Where does the PML live?

There is no PML object anywhere in the program. The absorber lives in two
places and nowhere else:

- **Layer 1**, as three scalars on `Simulation`: `absorber_um`,
  `absorber_order`, `absorber_loss_max` (lines 41–45). That is the whole
  user-facing description.
- **Layer 2**, as a graded loss profile inside `_graded_loss()` (line 74),
  immediately folded into `ce_a`, `ce_b`, `ch_a`, `ch_b`. After
  `discretize()` returns, the absorber has no separate existence.

Layer 3 contains zero lines of absorber code. `step()` runs the same two
array expressions over the whole grid; the interior cells simply have
loss = 0, so `ce_a = 1` and `ce_b = Sc` there and the updates reduce to
Schneider Eq. (3.18) / Eq. (3.15).

The termination used is the 1D matched lossy layer, not a true PML.
Schneider §11.2 works out that a lossy layer is reflectionless at normal
incidence when the electric and magnetic losses are matched, σ_m/μ = σ/ε
(Eq. 11.21); that makes η₂ = η₁ (Eq. 11.22) and therefore Γ = 0
(Eq. 11.20) at every frequency, and he notes it is the reason a lossy layer
"provided an excellent ABC for 1D grids" before generalising it to the
split-field PML (§11.4) and the un-split/CPML formulations (§11.5–11.6) that
2D and 3D need. The prototype implements exactly the matched condition: it
builds one dimensionless loss parameter L = σΔt/(2ε), samples it at the
integer E nodes and the half-integer H nodes, and uses the *same* L in both
coefficient pairs — `ce_a = (1−L)/(1+L)`, `ce_b = Sc/(1+L)`,
`ch_a = (1−L)/(1+L)`, `ch_b = Sc/(1+L)` (lines 106–109). Matching σ_m/μ to
σ/ε is what makes those two pairs identical. Schneider §11.2 also observes
that the conductivity should be raised gradually through the layer rather
than stepped; this uses the usual polynomial ramp, L(d) = L_max·(d/Δ)³ with
L_max = 0.45 over Δ = 20 cells, with PEC behind it.

Evidence that it works: `reflection ratio: 1.399e-04`, that is the peak
|Ez| at the monitor from the pulse coming back off an absorber, divided by
the incident peak (0.50). The split between "incident" and "return" is a
time gate at step 320, four pulse widths after the direct pulse passes the
monitor. Both returns are visible in the lower panel of the PNG at ~7e-5:
the one at step ~660 is the left-hand absorber's echo, the one at step
~1060 is the far end's. Two knobs move this number; the owner may want to
see the trade: raising `absorber_order` or `absorber_loss_max` too far makes
the grading too abrupt and the reflection climbs again.

## What is in `State`?

Four fields, at lines 141–148:

| Field | Shape | What it is |
| --- | --- | --- |
| `e` | `(nx,)` f64 | Ez at integer nodes, time n |
| `h` | `(nx-1,)` f64 | Hy at half nodes, time n+½ |
| `tm` | `(n_steps,)` f64 | the time-monitor buffer |
| `n` | `int` | step counter |

Nothing else in the program is mutable. There is no module-level array, no
scratch buffer, no accumulator hidden in the driver. The interesting one is
`tm`: spec §8.4 rule 5 says monitors accumulate into state and there are no
callbacks with side effects inside the step, and this is what that costs —
`step()` writes `tm = state.tm.copy()` then `tm[n] = ...` (lines 180–181),
so a 1700-element buffer is copied 1700 times per run even though one float
changed. Deleting just that copy (measured separately, same plan) moves the
run from 14.8 ms to 13.3 ms against 10.8 ms in place, so the monitor buffer
is about a third of the whole allocation gap on its own.

The step order is the spec's §8.4 order with the features this prototype
lacks removed: `update_h` → `update_e` → `inject_J` → `record_time` (no M
source, no ψ, no ADE poles, no DFT). The Appendix B pseudocode carries over
with no change of shape.

One thing the prototype does *not* settle: snapshots. `run()` collects E
arrays into a dict (line 186) outside `step()`, because a snapshot is not
state — it is output. The owner may want that to be a monitor kind instead.

## Is the functional style worth its allocation cost at this size?

Measured on a 800-cell grid over 1700 steps (40 µm at 20 cells/µm, Sc = 1,
f64, single-threaded NumPy), the same plan and the same math both ways,
`run_in_place()` (line 197) mutating three preallocated buffers and
`run()` (line 186) allocating fresh ones through the pure `step()`:

```
functional: 116,095 steps/s
in-place: 161,254 steps/s
ratio: 1.39
```

The two are asserted to produce identical monitor traces (`np.allclose`),
so this is a like-for-like comparison and not a comparison of two different
programs. 1.39× is inside the "~1.2–1.5× allocation overhead" band spec
§10 / §8.4 already predicts for the eager functional style. In absolute
terms both are far from being the bottleneck here: a full 1700-step run is
about 15 ms functional against 11 ms in place, and the whole script
including two runs and the figure is 0.7 s.

Three caveats the measurement carries, which the owner should weigh rather
than take from the ratio alone. The grid is 800 cells in 1D; the per-step
arrays are 6.4 kB and fit in L2, so allocation is a large fraction of a
step in a way it will not be at 3D sizes where the arithmetic dominates.
About a third of the gap is the monitor-buffer copy described above (1.5 ms
of the 4.0 ms difference), which is an artefact of storing the buffer in
`State` and would disappear under a chunked or write-once monitor. And `run_in_place()` is not the honest
in-place optimum either — it still allocates temporaries for
`plan.ch_b * (e[1:] - e[:-1])`; a fully fused version with `out=` arguments
would beat both. So 1.39 is an upper bound on what the functional style
costs at this size and, if anything, an over-estimate of what it will cost
at realistic ones.
