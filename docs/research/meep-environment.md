# Meep environment: conda spec, version pin, 2D smoke test

Resolves GitHub issue #11. Built and verified 2026-09-17 on the desktop (Ubuntu
24.04.5 LTS, kernel 7.0.0-31-generic, Ryzen 7 5700X3D, 16 threads), against
Meep's own installation docs, the `conda-forge/pymeep-feedstock` build matrix,
and — for everything in the version table — the environment that was actually
solved and installed on this machine. Nothing here is copied from a
second-hand write-up: the version numbers are `conda list` output, and the
flux number is this machine's own run.

## TL;DR

- **Pinned: `pymeep 1.34.0`, `nompi` variant, on Python 3.13.15, from
  conda-forge only.** Env name `waveyard-meep`, spec in
  [`envs/meep.yml`](../../envs/meep.yml). 1.34.0 is the newest version the
  feedstock has (`conda search -c conda-forge pymeep` lists nothing above it);
  3.13 is the ceiling, since the feedstock has no 3.14 build (issue #4).
- **`nompi`, deliberately.** conda-forge ships each pymeep build twice,
  `nompi_*` and `mpi_mpich_*`. The spec's Meep comparisons (§11.4 I2, I4) are
  single-process runs of small 2D/3D geometries; `nompi` keeps `mpich` and its
  launcher out of the environment, and every pymeep feature this project needs
  (`EigenModeSource`, mode decomposition, flux monitors) is in both variants.
  Switching later is a one-line edit to `envs/meep.yml` plus a re-lock.
- **Locked with `conda-lock` 4.0.2** into
  [`envs/conda-lock.yml`](../../envs/conda-lock.yml): 161 packages with URLs and
  hashes, `content_hash` (linux-64)
  `521e16445918abca549891797f53be4846c4b3832989fb2afef8f652e7884d6e`. The
  `conda list --explicit` fallback was not needed.
- **Smoke test runs in well under a minute.** `envs/meep_smoke_2d.py` takes
  **0.67 s** of Meep time (2.2–3.1 s wall including `conda run` startup and the
  MPB mode solve) and prints `flux at 1.55 um: 62.9287`.
- **conda was absent on this machine; Miniforge was installed to `~/miniforge3`
  without touching any shell rc file.** `conda init` was deliberately not run —
  see [Gotchas](#gotchas).

## What got pinned, and what it resolved to

`envs/meep.yml` asks for four things (`python=3.13`, `pymeep=1.34.*=nompi_*`,
`numpy`, `matplotlib`) and conda-forge pulls the rest. What the solver actually
produced, from `conda list -n waveyard-meep` (163 packages, 1.5 GB on disk):

| Package | Version | Build | Why it matters |
|---|---|---|---|
| python | 3.13.15 | `hf47f18c_103_cp313` | ceiling set by the feedstock's build matrix, not by us |
| pymeep | 1.34.0 | `nompi_py313h12ef16b_101` | the pin; `_101` is the current rebuild of 1.34.0 |
| mpb | 1.12.0 | `nompi_h9b57f5a_105` | MIT Photonic Bands — this is what makes `EigenModeSource` work |
| harminv | 1.4.3 | `h63ef21f_0` | harmonic inversion; the spec's I5 ring test (§11.4) wants it later |
| libgdsii | 0.21 | `h84d6215_5` | GDS import for Meep; deprecated upstream in favour of gdstk |
| numpy | 2.5.3 | `py313hb5f73ae_0` | same version the uv side resolves (issue #4), so arrays compare cleanly |
| scipy | 1.18.1 | `py313he2a5f1a_0` | pulled in by pymeep |
| matplotlib | 3.11.2 | `py313h4488465_0` | field plots for the comparison notebooks |
| h5py / hdf5 | 3.16.0 / 1.14.6 | `nompi_*` | Meep's output format; the `nompi` HDF5 follows from the `nompi` pymeep |
| fftw | 3.3.11 | `nompi_h3b011a4_100` | ditto |
| gsl | 2.8 | `h3cd6761_2` | the dependency behind the feedstock's most recent rebuild |
| libopenblas | 0.3.34 | `pthreads_hf13c14d_2` | pthreads variant, not OpenMP |

Two things worth noticing. First, `numpy` resolved to **2.5.3**, the same
version the uv-managed side of the project resolves (see
`docs/research/python-deps.md`) — so arrays can be moved between the two
environments by value without a version mismatch in the pickle/npz format.
Second, the whole chain is consistently `nompi_*`: asking for the `nompi`
pymeep forces `nompi` HDF5, h5py, and FFTW too, which is exactly the point of
the variant.

Meep's docs are unambiguous that conda is the supported route — the
installation page recommends "the Conda package manager" for PyMeep
([meep.readthedocs.io/en/latest/Installation](https://meep.readthedocs.io/en/latest/Installation/)),
and there is still no PyPI distribution, which is why this environment exists
separately from the project's `uv` venv at all
([conda-forge/pymeep-feedstock](https://github.com/conda-forge/pymeep-feedstock)).

## How the lockfile was produced

`conda-lock` installed and ran cleanly on the first try, so the fallback
(`conda list -n waveyard-meep --explicit > envs/meep.lock.txt`) was not used:

```sh
uvx conda-lock lock -f envs/meep.yml -p linux-64 \
    --conda ~/miniforge3/bin/mamba --lockfile envs/conda-lock.yml
```

`uvx` runs conda-lock ephemerally (version 4.0.2 today), so the project takes
on no new permanent tool, and `--conda ~/miniforge3/bin/mamba` points it at the
solver we actually install with. Two details:

- **Pass `--lockfile envs/conda-lock.yml`.** Without it conda-lock writes
  `conda-lock.yml` into the *current directory*, not next to the source env
  file. The first run here dropped it in the repo root.
- The lockfile records the platform it was solved for. Only `linux-64` is
  locked; the laptop and desktop are both linux-64, and osx/win were not solved
  for because nothing in this project runs there.

Re-solving after editing `envs/meep.yml` is the same command again. Updating a
single package is `uvx conda-lock lock --lockfile envs/conda-lock.yml --update <pkg>`.

Installing *from* the lockfile (`conda-lock install -n waveyard-meep
envs/conda-lock.yml`) is **not** verified here — the environment on this
machine was built from `envs/meep.yml`, and the lock was produced afterwards as
the reproducibility record. Someone should try the lockfile install path on the
laptop before trusting it as the primary route.

## The smoke test

[`envs/meep_smoke_2d.py`](../../envs/meep_smoke_2d.py) is a 2D straight silicon
waveguide: a 0.5 µm wide n = 3.48 core in n = 1.444 cladding, 10 × 4 µm cell,
1 µm PML on all sides, resolution 20 (pixels/µm, so a 200 × 80 grid), one
`mp.EigenModeSource` with a Gaussian centred at 1.55 µm, one `mp.FluxRegion`
3 µm downstream, run with `mp.stop_when_fields_decayed`. Constant indices, not
a Lorentz fit, because that is what §11.4 I2/I4 specify for the comparison.

It is deliberately the seed of the later comparison rather than a throwaway
`import meep`: it exercises the two features I2 and I4 actually depend on
(`EigenModeSource`, which needs MPB as a separate shared library, and flux
monitoring), so it fails loudly if either half of the install is broken.

Output on this machine:

```
MPB solved for frequency_1(2.10352,0,0) = 0.645161 after 3 iters
run 0 finished at t = 150.075 (6003 timesteps)
flux at 1.55 um: 62.9287
meep version: 1.34.0
wall time: 0.67 s
```

Timings: **0.67 s** inside Meep, 2.2–3.1 s of wall clock for the whole
`conda run` invocation (the spread is interpreter and library import). Nowhere
near the one-minute budget, so resolution has room to grow when this becomes a
real comparison.

One physical sanity check, worth recording because it is the first number this
project has out of a reference solver: MPB converged on k = 2.10352 (in Meep's
units of 2π/a, a = 1 µm) at f = 0.645161 = 1/1.55 µm⁻¹, i.e. **n_eff ≈ 3.260**
for the fundamental Ez mode. That is a 2D slab, not the 3D 500 × 220 nm strip,
so it should *not* match the 2.44 that §11.3 M2 quotes — it sits between the
core index and the cladding index and much nearer the core, which is what a
0.5 µm slab at 1.55 µm should do. The flux value 62.9 is in Meep's arbitrary
units and is only meaningful as a ratio against a second monitor; the eventual
I4 comparison normalises it against a no-waveguide reference run.

## Recreating this from scratch

On a machine with no conda at all (the desktop today):

```sh
# 1. Miniforge (conda-forge's own installer; no shell rc changes)
curl -L -o /tmp/Miniforge3.sh \
    https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash /tmp/Miniforge3.sh -b -p ~/miniforge3

# 2. The environment (about 15 s on this machine, 1.5 GB on disk)
~/miniforge3/bin/mamba env create -f envs/meep.yml

# 3. Re-lock, only when envs/meep.yml changes
uvx conda-lock lock -f envs/meep.yml -p linux-64 \
    --conda ~/miniforge3/bin/mamba --lockfile envs/conda-lock.yml

# 4. Smoke test
~/miniforge3/bin/conda run -n waveyard-meep python envs/meep_smoke_2d.py
```

Versions this session used: Miniforge's `conda 26.7.2` and `mamba 2.9.0`,
`conda-lock 4.0.2`.

## Gotchas

1. **`conda init` was not run, on purpose.** The installer was run with `-b`
   (batch) and no rc file was touched, so `conda` is not on `PATH` and no base
   environment is auto-activated in new shells. Everything above uses the full
   path `~/miniforge3/bin/conda`. The owner can opt in whenever they like with
   `~/miniforge3/bin/conda init bash` (then open a new shell); `conda config
   --set auto_activate_base false` keeps the prompt clean afterwards. Leaving
   this to the owner also keeps the `uv`-managed project venv the default
   Python, which is what the rest of the repo assumes.
2. **This environment is not, and cannot be, the project venv.** pymeep is not
   pip-installable at all. Meep code runs under `conda run -n waveyard-meep`;
   waveyard code runs under `uv run`. Anything shared between them crosses as
   data on disk (`.npz`/HDF5), not as an import. That is a constraint on how the
   I2/I4 comparison is written: a Meep script produces a file, a pytest under
   the `meep` marker reads it.
3. **The `nompi`/`mpi_mpich` split infects the whole dependency chain.** Mixing
   an `mpi_mpich_*` pymeep into this environment later means re-solving HDF5,
   h5py and FFTW too. Change it in `envs/meep.yml` and re-lock; do not
   `conda install` it on top.
4. **Pin the build string, not just the version.** `pymeep=1.34.*` alone can
   resolve to either variant. The spec is `pymeep=1.34.*=nompi_*`, where the
   third field is the build string glob.
5. **`conda run` swallows and re-emits output.** It prints Meep's own
   `Elapsed run time` after the script's own prints; the script therefore prints
   its own `time.perf_counter()` measurement so the timing in this doc is a
   number we control.
6. **Resolution 20 is a smoke-test number, not a comparison number.** §11.4 I2
   requires *identical* Δ between waveyard and Meep. When the comparison is
   written, the resolution comes from the shared plan, not from this file's
   constant.
7. **1.5 GB for one environment.** Meep itself is 6 MB of it. The bulk is
   `matplotlib`'s Qt chain, which drags in LLVM and clang as *runtime* libraries
   (`libLLVM.so` 188 MB, `libclang-cpp.so` 94 MB, `libclang.so` 55 MB, qt6
   87 MB, PySide6 45 MB). If disk becomes tight on the laptop, swapping
   `matplotlib` for `matplotlib-base` in `envs/meep.yml` drops the Qt/PySide6
   backend — and most of that chain — at the cost of interactive plot windows;
   file output still works.

## Unverified / flagged for follow-up

- `conda-lock install -n waveyard-meep envs/conda-lock.yml` — the lock was
  produced but never installed *from*. Worth one run on the laptop.
- The `mpi_mpich` variant was not built or benchmarked; whether MPI is worth it
  for the 3D I2 comparison is an open question for whoever writes that test.
- No comparison against waveyard exists yet: this doc establishes the reference
  environment only. The flux number above is a reproducibility anchor, not a
  validated physical result.
- Whether the feedstock ever gains a Python 3.14 build (still no sign of one) —
  the cap in `envs/meep.yml` should be revisited when it does.
