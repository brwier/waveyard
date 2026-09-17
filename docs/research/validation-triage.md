# Validation triage: which §11 tests survive the learning re-cut

**Status: proposal. The owner decides.** This document is the analysis half of
the grilling ticket "Validation tests: which survive the re-cut and when each
is earned". Nothing here is settled; the table is a starting position to be
argued with, not a plan.

Spec [v0.1 §11](../spec/v0.1.md) defines 27 validation items across six
groups. Spec §13 assigned each of them to the original product-first milestone
order (M0 skeleton → M1 mode solver → M2 geometry → M3 stepper → M4 ports →
M5 GPU/Meep → M6 workflow). The map (issue #1) reordered the milestones
**stepper-first**, and issue #6 carries the reordered sequence. This document
re-hangs every §11 test on that new order and recommends keep, defer, or drop.

## The re-cut, in the four sentences that drive the triage

1. **The owner writes the core.** A test is worth most when it is the thing
   that tells the owner their own stepper, plan, or mode solver is right.
   Tests that only guard agent-written scaffolding earn less.
2. **1D first, then 2D; 3D stays the v1.0 target.** Any test whose cheapest
   honest form is 1D or 2D moves early; anything that needs 3D moves late but
   is not deleted.
3. **Libraries arrive when they solve a felt problem.** A test that drags in a
   new dependency (hypothesis, femwell, Meep, torch) is scheduled at the
   milestone where that dependency is already being introduced with a lesson.
4. **Product credibility is demoted, not dropped.** The Meep comparison, the
   analytic suite, and the ROCm benchmark stay. What changes is *when* they
   are earned and whether they gate CI.

## Proposed milestone list (stepper-first)

| Label | Milestone | What the owner builds |
|---|---|---|
| L1 | 1D stepper | 1D FDTD through all three layers: dataclasses object model → plain-array plan → NumPy backend. Gaussian pulse, time monitor, PML. Constant index. |
| L2 | 2D | The same stepper widened to 2D. First transverse structure, first field plots. |
| L3 | Mode solver | Finite-difference mode solver: 1D slab, then 2D strip cross-section. n_eff, n_g. |
| L4 | Geometry & materials | GDS → permittivity rasterizer, material fits, Lorentz ADE in the stepper. |
| L5 | Ports & S-parameters | Mode source, DFT mode monitors, overlaps, `sparameters()`. 2D devices. |
| L6 | torch backend & GPU | array-api-compat, torch CPU, torch ROCm on the desktop, benchmarks. |
| L7 | gdsfactory workflow | `from_component`, `write_sparameters`, export. Docs and release optional. |

"§13 M*" below refers to the **old** milestone numbering. "M1–M4" in the id
column are the **mode-solver test ids** from §11.3, which unfortunately share
letters with the old milestones; they are always the ids when in the id column.

## The table

Every test in §11 appears exactly once.

| id | test | old milestone (§13) | proposed (stepper-first) | keep/defer/drop | reasoning |
|---|---|---|---|---|---|
| U1 | Object model: validation errors on bad units, zero-size planes, sources outside the domain, monitors inside PML, non-Manhattan ports | M0 | L1 (ports and plane checks at L5) | keep, split | The object model is the first layer the owner writes at L1, so its validation errors are the first thing that can be tested at all; but "non-Manhattan port" and plane-size rules have no referent until ports exist at L5, so testing them earlier tests a fiction. |
| U2 | Plan: coefficients match hand-computed values for uniform media, PML profiles monotone, waveform spectrum (FFT) | M0 / M3 | L1 | keep, promote | This is the single best test of the re-cut: hand-computing a 1D update coefficient and asserting the plan matches it is exactly the "do I understand the numerics" check the owner needs, and it needs nothing but NumPy. |
| U3 | Rasterizer (hypothesis): fill fractions in [0,1], sum ≤ 1, exact for axis-aligned rectangles, converges for rotated ones, gdstk keyholes | M2 | L4 | keep | Property-based testing is the felt problem that justifies introducing hypothesis, and the rasterizer is the only place in the project where it pays for itself; it lands with geometry, not before. |
| U4 | Materials: `from_nk` fits reproduce tabulated n within residual; `eps(λ)` matches the ADE steady state (single-cell oscillator) | M2 / M3 | L4 | keep | The single-cell oscillator test is the cheapest way to verify an ADE before it is loose in a full grid, so it must precede A3 in the same milestone; it is meaningless before Lorentz media exist at L4. |
| A1 | Pulse propagation: 1D free space, group velocity = 1 within numerical-dispersion prediction at Δ = λ/20 | M3 | L1 | keep, promote | This is L1's acceptance test. A Gaussian pulse that travels at the right speed is the first evidence the owner's own stepper works, and numerical dispersion is the first physics lesson the milestone teaches. |
| A2 | Fresnel: 1D half-space, n = 2 and Lorentz-fit Si, R and T within 1% at 21 wavelengths | M3 | L1 (n = 2); Lorentz variant at L4 | keep, narrowed | The constant-index half is nearly free once L1 runs and catches sign and interface-averaging errors immediately; the Lorentz-fit half is an ADE test wearing a Fresnel costume and belongs with materials. |
| A3 | Lorentz slab: 1D 1 µm slab, 1-pole medium, complex T vs transfer matrix, \|ΔT\| < 0.01, phase < 2° | M3 | L4 | keep, deferred | The only test that pins ADE correctness against an independent analytic model, so it cannot be dropped; but it is 1D, which means L4 can earn it without waiting for 2D or 3D dispersive runs. |
| A4 | PML normal: 1D and 3D plane wave into PML, reflected power ≤ −40 dB | M3 | L1 (1D); 3D variant deferred to the 3D era | keep, split | The 1D PML is built at L1, so its reflection floor is the acceptance test for the hardest part of that milestone; the 3D variant tests nothing new about the owner's understanding and waits until a 3D plan exists. |
| A5 | PML oblique: 2D at 45°, ≤ −30 dB | M3 | L2 | keep | This is L2's acceptance test and the first thing that genuinely requires two dimensions — a 1D PML that looks perfect can still fail at angle, which is the point of the milestone. |
| A6 | Energy: closed PEC box, lossless inclusion, dipole then off, stored energy constant to 1e-3 (fp32) over 5000 steps | M3 | L2 (a 1D form as a smoke test at L1) | keep | Energy conservation is the best whole-stepper correctness check that needs no analytic reference at all, and 5000 steps of a small 2D box is seconds on the laptop. |
| A7 | Convergence: DC-A \|S21\| at Δ = 40/30/20/15 nm, monotone, observed order ≥ 1.5 | M4 | L5 as written; **candidate to re-earn at L1/L2** | keep, but re-scope | As written this waits for a directional coupler and working S-parameters, which puts the project's only order-of-accuracy check four milestones after the stepper is written. A 1D convergence study on A1's group velocity or A2's Fresnel R would earn the same lesson at L1. See the questions. |
| A8 | Mode source directivity: straight waveguide, monitors both sides, backward/forward ≤ −30 dB | M4 | L5 | keep | It cannot exist before the mode source does, and §14 names mode-source leakage a medium-likelihood risk that corrupts every S-parameter, so it is the first test L5 should write rather than the last. |
| M1 | Symmetric slab: TE/TM n_eff vs analytic transcendental to 1e-6 (1D) | §13 M1 | L3 | keep, promote | The mode solver's first acceptance test, analytic, 1D, and tight to 1e-6 — the cleanest "your solver is exactly right" signal anywhere in §11, and it should be written before the 2D solver exists. |
| M2 | Strip 500 × 220 nm Si/SiO₂ at 1.55 µm: TE0 n_eff = 2.44 ± 0.01, TM0 ≈ 1.78 ± 0.02 at Δ = 20 nm, convergence documented | §13 M1 | L3 | keep | The number every silicon-photonics reader already knows, so it is the milestone's shareable artifact as well as its test; the documented Δ-convergence doubles as the mode solver's own order check. |
| M3 | Cross-check against femwell in a notebook (not CI) | §13 M1 | after L3, optional | defer | M1's analytic check already pins correctness to 1e-6, so femwell adds a second opinion but also a library the re-cut has no other felt need for; worth keeping as an optional notebook, not as a gate. |
| M4 | n_g of the strip ≈ 4.2 ± 0.1 | §13 M1 | L3 | keep | Group index is derived from n_eff(λ) with a few lines, and everything downstream — S-parameter phase at I1, resonance spacing if a ring ever returns — depends on it being right. |
| I1 | Straight waveguide (3D, Lorentz Si): \|S21\| ≥ 0.995, \|S11\| ≤ −40 dB, arg(S21) matches β(λ)·L within 3° | M4 | L5 in 2D; 3D form stays the v1.0 acceptance | keep, narrowed | The phase-vs-β·L check is the test that ties the mode solver and the stepper together, and it works in 2D with an effective index; the 3D run is the same test on hardware the owner now has, so it stays as the v1.0 target rather than the first attempt. |
| I2 | Directional coupler vs Meep (3D, conda-forge Meep, identical constant-index materials and Δ) | M5 | L6 era, **after I4** | keep, reordered | This is the headline credibility artifact and survives the demotion, but meeting Meep for the first time in 3D means debugging the comparison and the 3D stepper at once; the 2D version should come first. |
| I3 | Coupler vs coupled-mode theory: coupling length from even/odd n_eff within 5% | M5 | L5 | keep, promote | Pure physics cross-check with no new dependency, and it reuses the L3 mode solver directly — the cheapest way to know the coupler is right before Meep is involved at all. |
| I4 | 2D coupler vs Meep 2D with the same effective indices, same tolerances | M5 (parenthesised) | L5/L6, **first Meep contact** | keep, promoted | A parenthetical in §13 becomes the primary Meep test under a 2D-first re-cut: it runs on the laptop, isolates the comparison machinery from 3D cost, and makes I2 a re-run rather than a first attempt. |
| I5 | Ring resonator (v1 SHOULD): resonances vs n_g and ring length within 0.5 nm | M5 (SHOULD) | — | drop from v0.2 | §13's own cut line already names the ring the first thing dropped, and the re-cut has less budget, not more; it teaches nothing the coupler has not, and it returns naturally with harmonic inversion in v1.2. |
| P1 | `numpy` vs `torch` CPU: relative L2 field difference < 1e-5 after 100 and 1000 steps | M5 | L6 | keep | Backend parity *is* the felt problem that justifies array-api-compat and torch, so this test is the reason L6 exists rather than an afterthought of it. |
| P2 | `torch` CPU vs `torch` ROCm: < 1e-4 | M5 | L6 | keep | The desktop and ROCm 7.2 are now confirmed working, so this is an acceptance test the project can actually run; the looser tolerance teaches why reduction order matters. |
| P3 | S-parameters across backends: \|ΔS\| < 1e-4 (torch), < 1e-3 (wgpu, v1.1) | M5 | L6 (torch only) | keep, narrowed | Field parity can pass while a reduction inside the mode overlap differs, so the S-parameter form is worth its own row; the wgpu column is v1.1 and out of scope for this map. |
| P4 | Saved-plan round trip: identical results from a `.npz` plan | — (unlisted in §13) | L1 or L2 | keep, promote | The cheapest possible proof of the architecture's central claim — that a plan is inert data — and it is available the moment a plan exists, long before any backend needs comparing. |
| R1 | Golden S-parameter regression files for I1–I4 under `tests/golden/`; any change beyond tolerance fails CI | M4 / M5 (CI) | L5, scoped to whichever of I1/I3/I4 survive | keep, scoped | Golden files are what keep a refactor from silently changing physics, which matters most once the owner starts rewriting their own stepper; but they can only be generated after the first trusted S-parameter run. |
| B1 | `bench` tests run manually and append to `benchmarks/results.jsonl` | M5 | L6 | keep | The ROCm benchmark is one of the two artifacts §13 says carries the most weight, it costs almost nothing once the torch backend runs, and cell·steps/s is the number that makes the GPU milestone feel real. |

## Summary of the movement

- **Promoted into L1/L2** (earned four milestones earlier than §13): U2, A1, A2 (constant-index), A4 (1D), P4, and — if the owner agrees — A7 in a 1D form.
- **Held where they are, re-labelled**: U3, U4, A3, A5, A6, A8, M1, M2, M4, I3, P1, P2, P3, B1.
- **Reordered against each other**: I4 before I2 (2D Meep before 3D Meep); I1 in 2D before I1 in 3D.
- **Demoted to optional**: M3 (femwell).
- **Dropped from v0.2**: I5 (ring), and the wgpu half of P3 (v1.1, already out of scope).
- **Split across milestones**: U1 (object model now, ports later), A2 and A4 (1D now, dispersive/3D later).

Net: 24 of 27 items survive intact or narrowed, 1 is demoted to optional, 1 is
dropped, and 1 (A7) is the open question below.

## Questions for the grilling

- **Does A7 survive without DC-A?** As written, the project's only
  order-of-accuracy check waits for a directional coupler and working
  S-parameters at L5. A 1D convergence study — group velocity from A1, or
  Fresnel R from A2, at Δ = 40/30/20/15 nm — earns the same lesson at L1 for
  almost no cost. Is A7 re-scoped to 1D at L1, kept as-is at L5, or both?
- **Does I5 drop, or become a stretch notebook?** §13's cut line already names
  the ring first to go, but it is also the most photonics-shaped thing in §11
  and the only test that would exercise a long high-Q run. Drop it from v0.2
  entirely, or keep it as an unscheduled notebook the owner may do for fun?
- **Is I4 the first Meep contact, ahead of I2?** The 2D comparison runs on the
  laptop and isolates the comparison machinery from 3D cost — but it also means
  the headline 3D artifact arrives later. Is that an acceptable trade for a
  smoother first encounter with Meep?
- **When is 3D first exercised at all?** The map keeps 3D as the v1.0 target,
  but under this triage no test requires it before L6/L7 (A4-3D, I1-3D, I2).
  Does some milestone own "make it run in 3D", or does 3D arrive as a late
  widening with its own acceptance?
- **Does the femwell cross-check (M3) survive?** It is a genuinely independent
  check of the mode solver the owner writes by hand, which is exactly where an
  independent check is most valuable — against a new library the re-cut has no
  other need for. Optional notebook, scheduled lesson, or cut?
- **Which tests gate CI now that product credibility is demoted?** §12 has
  unit + analytic on every push and integration nightly. Under the re-cut, does
  R1 gate CI from L5 onward, or does the golden-file discipline wait until the
  owner stops rewriting the stepper weekly?
