# Python and dependency compatibility for the laptop environment

Resolves GitHub issue #4. Verified 2026-09-17 on Ubuntu 26.04 x86_64, `uv 0.12.6`,
against PyPI's own JSON API (`https://pypi.org/pypi/<name>/json`), each project's own
docs, and the `conda-forge/pymeep-feedstock` repo. Empirical cross-check: `uv venv
--python 3.12|3.13|3.14` + `uv pip install --dry-run <spec>` in this worktree (no
real installs were performed for the heavy packages; torch was dry-run only).

## TL;DR

- **`requires-python = ">=3.12,<3.15"`.** Every spec dependency has a working wheel
  on 3.12, 3.13 *and* 3.14 today (verified both from PyPI JSON metadata and by an
  actual `uv` dry-run resolve on all three interpreters). The `<3.15` ceiling isn't
  our choice — `gdsfactory` 9.51.0 itself declares `requires_python: "<3.15,>=3.12"`
  on PyPI, so 3.15 is blocked upstream regardless of what we pick.
- **Default dev interpreter: Python 3.12** (matches the repo's current
  `requires-python`, has the longest track record of the three). 3.13 and 3.14 are
  verified-working alternatives; see the table below.
- **Meep/pymeep stays conda-forge-only.** There is no PyPI wheel or sdist for it. If
  it's ever wired in (e.g. for cross-checking the FDTD stepper against a reference
  solver), it needs its own conda environment, separate from the uv venv, and that
  conda environment currently tops out at **Python 3.13** (no 3.14 build yet as of
  the feedstock's 2026-08-08 rebuild).
- **Recommended extras layout** (`pyproject.toml`):

  ```toml
  [project]
  requires-python = ">=3.12,<3.15"
  dependencies = []

  [project.optional-dependencies]
  core = ["numpy>=2", "scipy", "pydantic>=2", "xarray", "matplotlib", "array-api-compat"]
  gds  = ["opencv-python-headless", "gdsfactory>=9", "gdstk"]
  torch = ["torch"]
  wgpu = ["wgpu"]
  dev  = ["pytest", "ruff", "mypy"]

  # Pin torch to the CPU wheel index by default. Swap the url to a ROCm index
  # later (e.g. https://download.pytorch.org/whl/rocm7.2, verified today to carry
  # the same torch==2.14.0 release with cp312/cp313/cp314 wheels) — no
  # requires-python change needed for that swap.
  [tool.uv.sources]
  torch = [{ index = "pytorch-cpu" }]

  [[tool.uv.index]]
  name = "pytorch-cpu"
  url = "https://download.pytorch.org/whl/cpu"
  explicit = true
  ```

  This keeps the repo's existing convention (`dependencies = []`, everything opt-in
  through extras) and adds `core`/`gds`/`torch`/`wgpu` alongside the existing `dev`.

- **Install commands** (from a fresh clone):

  ```bash
  uv venv --python 3.12
  uv sync --extra core --extra gds --extra wgpu --extra dev
  uv sync --extra torch          # pulls torch==2.14.0+cpu via the pinned index above
  ```

  Or, without wiring the index into `pyproject.toml` (ad hoc, e.g. to test a
  different interpreter):

  ```bash
  uv venv --python 3.13
  uv pip install -e ".[core,gds,wgpu,dev]"
  uv pip install torch --extra-index-url https://download.pytorch.org/whl/cpu \
      --index-strategy unsafe-best-match
  ```

## Dependency table

Wheel columns are for **linux x86_64** (the target laptop), checked against the
`releases[<latest version>]` file list in each package's PyPI JSON API response,
cross-checked with an empirical `uv pip install --dry-run` resolve on each
interpreter (all three resolved cleanly, no backtracking failures, no missing
wheels).

| Package | Latest (PyPI, 2026-09-17) | `requires_python` | py3.12 | py3.13 | py3.14 | Source / note |
|---|---|---|---|---|---|---|
| numpy | 2.5.3 | `>=3.12` | yes | yes | yes | `cp312`/`cp313`/`cp314` manylinux wheels. [pypi.org/pypi/numpy/json](https://pypi.org/pypi/numpy/json) |
| scipy | 1.18.1 | `>=3.12` | yes | yes | yes | `cp312`/`cp313`/`cp314` manylinux wheels. [pypi.org/pypi/scipy/json](https://pypi.org/pypi/scipy/json) |
| pydantic | 2.13.5 | `>=3.9` | yes | yes | yes | Pure-Python `py3-none-any` wheel; compiled core is `pydantic-core` 2.49.0 (`requires_python >=3.10`), which does ship `cp312`/`cp313`/`cp314` manylinux wheels. [pypi.org/pypi/pydantic/json](https://pypi.org/pypi/pydantic/json), [pypi.org/pypi/pydantic-core/json](https://pypi.org/pypi/pydantic-core/json) |
| xarray | 2026.7.0 | `>=3.11` | yes | yes | yes | Pure-Python `py3-none-any` wheel. [pypi.org/pypi/xarray/json](https://pypi.org/pypi/xarray/json) |
| matplotlib | 3.11.2 | `>=3.11` | yes | yes | yes | `cp312`/`cp313`/`cp314` manylinux wheels. [pypi.org/pypi/matplotlib/json](https://pypi.org/pypi/matplotlib/json) |
| array-api-compat | 1.15.0 | `>=3.10` | yes | yes | yes | Pure-Python `py3-none-any` wheel. [pypi.org/pypi/array-api-compat/json](https://pypi.org/pypi/array-api-compat/json) |
| opencv-python-headless | 5.0.0.93 | `>=3.6` | yes | yes | yes | Single `cp37-abi3` manylinux wheel (stable-ABI, forward compatible) — confirmed installable on 3.14 by dry-run, not just tag arithmetic. [pypi.org/pypi/opencv-python-headless/json](https://pypi.org/pypi/opencv-python-headless/json) |
| gdsfactory | 9.51.0 | **`<3.15,>=3.12`** | yes | yes | yes | Pure-Python `py3-none-any` wheel; upstream `requires_python` is the actual source of the `<3.15` ceiling in this doc's recommendation. Transitive deps (klayout, shapely, scikit-image, trimesh, …) all resolved cleanly on 3.12/3.13/3.14 in the dry-run. [pypi.org/pypi/gdsfactory/json](https://pypi.org/pypi/gdsfactory/json) |
| gdstk | 1.0.1 | `>=3.9` | yes | yes | yes | Explicit `cp312`/`cp313`/`cp314`/`cp314t` manylinux wheels (only package here with a native 3.14t free-threaded build). [pypi.org/pypi/gdstk/json](https://pypi.org/pypi/gdstk/json) |
| torch (CPU) | 2.14.0+cpu | `>=3.10` (PyPI default build) | yes | yes | yes | `https://download.pytorch.org/whl/cpu/torch/` index lists `cp312`/`cp313`/`cp314`/`cp314t`, and already `cp315` for 2.14.0. Confirmed via `uv pip install --dry-run torch --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match` on all three interpreters. |
| torch (ROCm, for later) | 2.14.0+rocm7.2 | same | yes | yes | yes | `https://download.pytorch.org/whl/rocm7.2/torch/` also has 2.14.0 with the same cp312/313/314(t) tag set. Note: `rocm7.1` index still lags at torch 2.13.0 — pick the ROCm minor that has parity with the CPU build you want. Exact ROCm-version-to-GPU (gfx target) compatibility is **unverified here** — tracked separately (see branch `research/rocm-rx9070xt`). |
| wgpu | 0.32.0 | `>=3.11` | yes | yes | yes | `py3-none-<platform>` wheels (ctypes wrapper around a bundled native `wgpu-native` binary, not a CPython-ABI-specific extension) — same wheel serves every Python 3.x. [pypi.org/pypi/wgpu/json](https://pypi.org/pypi/wgpu/json) |

## Meep / pymeep

- **No PyPI package.** `pymeep` returns 404 on `https://pypi.org/pypi/pymeep/json`.
  The name `meep` *does* exist on PyPI (v1.0.6) but it is an unrelated "very
  light-weight task runner" by Fredrik Håård (bitbucket.org/metallapan/meep) — not
  the NanoComp/Simpetus FDTD tool. Confirmed by reading that package's own metadata.
- Meep's own docs are explicit: *"The recommended way to install PyMeep is using
  the Conda package manager."* — [meep.readthedocs.io/en/latest/Installation](https://meep.readthedocs.io/en/latest/Installation/)
  (the docs also note `libGDSII` is deprecated in favor of `gdstk`, which is
  already in this project's spec).
- Current build: `conda-forge/pymeep-feedstock`, recipe version **1.34.0**
  ([recipe/meta.yaml](https://github.com/conda-forge/pymeep-feedstock/blob/main/recipe/meta.yaml)),
  last re-rendered **2026-08-08** (commit `891d1b0`, "Rebuild for gsl 2.8").
  Its CI build matrix (`.ci_support/*.yaml`) currently pins **Python 3.10, 3.11,
  3.12, 3.13** for linux-64/aarch64/ppc64le and osx-64/arm64, for both `mpich` and
  `nompi` variants. **No 3.14 build exists yet** as of this snapshot.
- Forced consequence: if Meep is added later (e.g. as a validation reference), it
  must run in its own conda env capped at Python 3.13 — it cannot share the uv venv
  regardless of the venv's Python version, since it isn't pip-installable at all.

## Decisions forced

1. **`requires-python` ceiling is set by `gdsfactory`, not by us.** Its PyPI
   metadata is `requires_python: "<3.15,>=3.12"`. Even though every other package
   in the spec (including torch and wgpu) already has working 3.14 wheels, picking
   anything with an upper bound above `<3.15` would be meaningless while
   `gdsfactory>=9` is in the spec.
2. **OpenCV is fine today; no substitution needed.** `opencv-python-headless`
   ships one `cp37-abi3` wheel per platform, and it installed cleanly (dry-run) on
   3.12/3.13/3.14 in this environment — the stable ABI tag isn't just a hopeful
   read of the filename, it's a working resolve. If it ever does lag a future
   CPython release, the natural fallback needs **no new dependency family**:
   `gdsfactory`'s own transitive closure already pulls in `scikit-image` and
   `shapely` (confirmed present in the dry-run resolution), either of which can do
   polygon rasterization (`skimage.draw.polygon`, or `shapely` geometry ->
   `rasterio`/`PIL.ImageDraw`) without adding a new library to the spec.
3. **array-api-compat's torch coverage is real but has sharp edges that matter for
   a stepper.** Per `array-api-compat`'s own docs
   ([data-apis.org/array-api-compat/supported-array-libraries.html](https://data-apis.org/array-api-compat/supported-array-libraries.html)):
   - Torch tensors are not wrapped — `array_namespace()`/`to_device()` helpers must
     be used explicitly (no native `__array_namespace__` on `torch.Tensor`).
   - **Slices with negative steps are not supported.** A Yee-grid stepper that
     leans on `field[::-1]`-style reversal (common in PML/mirroring code) will not
     be backend-portable as written; it needs to go through `torch.flip`/an
     explicit index array instead of relying on the array-API slice protocol.
   - Torch's **0-D tensor type promotion differs from the spec at the operator
     level** (`x + y`) — only the *functional* form (`xp.add(x, y)`) is patched to
     match the standard. Decision: write the hot update loop using the array-API
     functional calls, not Python operators, if numpy/torch backend parity is a
     goal.
   - `unique_all()` is unimplemented for torch (unlikely to matter for an FDTD
     stepper); `std()`/`var()` lack the `correction` kwarg; unsigned integer types
     other than `uint8` aren't supported.
   - Net effect: array-api-compat's torch support is sufficient for a functional
     stepper **as long as the update kernel is written as explicit
     array-API function calls and avoids negative-step slicing**, not as a
     drop-in "just import torch and it behaves like numpy" guarantee.
4. **Meep must live outside the uv-managed venv, capped at Python 3.13, for as
   long as `pymeep-feedstock` has no 3.14 build.** This is independent of whatever
   `requires-python` this project picks, since pymeep is conda-only either way.

## Unverified / flagged for follow-up

- Exact ROCm-version-to-GPU (gfx target) support matrix for the RX 9070 XT — out
  of scope here, already tracked on branch `research/rocm-rx9070xt`.
- Full runtime test-suite pass (not just dependency resolution) of the spec stack
  on Python 3.14 — this doc verifies wheel availability and clean `uv` resolution,
  not that every package's own test suite is green on 3.14.
- Any published timeline for a `pymeep` 3.14 conda-forge build — none found; the
  feedstock's CI matrix is the only evidence checked.
