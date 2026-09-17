# Curriculum Sources: FDTD Architecture and Modern Python

Answers [issue #3](https://github.com/brwier/waveyard/issues/3), "Primary sources for
the curriculum: FDTD architecture and modern Python." Seeds `learning/RESOURCES.md`
in the `teach` skill's format (Knowledge / Wisdom). Every URL below was fetched
directly during research (not recalled from memory); anything that could not be
verified this way is called out under **Gaps** instead of listed as fact.

Research date: 2026-09-17.

## Knowledge

### 1. FDTD fundamentals (refresher)

- [Book (free): _Understanding the Finite-Difference Time-Domain Method_ by John B. Schneider](https://eecs.wsu.edu/~schneidj/ufdtd/) — **RECOMMENDED READ for this topic**
  Free, chapter-by-chapter (and single-PDF) online book by an IEEE Fellow known for FDTD work; CC BY-SA 4.0; live and current as of today. Use for: **Ch. 3** ("FDTD in 1D") as the 1D refresher, **Ch. 11** ("Perfectly Matched Layer") for PML/CPML, **Ch. 10** ("Dispersive Material") for ADE dispersive media. Deliberately skip Ch. 14 (near-to-far-field) — not needed for this curriculum. Source mirror (in case the WSU host ever goes down): [github.com/john-b-schneider/uFDTD](https://github.com/john-b-schneider/uFDTD).
- [Book: _Computational Electrodynamics: The Finite-Difference Time-Domain Method_, 3rd ed., Taflove & Hagness (Artech House, 2005, ISBN 978-1-58053-832-9)](https://books.google.com/books/about/Computational_Electrodynamics.html?id=n2ViQgAACAAJ)
  The field's definitive reference text — deeper and more rigorous than Schneider, and the standard citation in nearly every FDTD paper (already cited in `docs/spec/v0.1.md` §17 for ADE media and CPML). Not free. Use for: looking up derivations and edge cases Schneider only sketches, once past the refresher stage. (Artech House's own product pages returned HTTP 403 on direct fetch — see Gaps — so the Google Books page above is given as the verified stable citation instead.)
- [Docs: Meep — "Introduction" § Finite-Difference Time-Domain Methods](https://meep.readthedocs.io/en/latest/Introduction/#finite-difference-time-domain-methods)
  Official Meep documentation's own description of the Yee lattice, Courant factor, and how Meep's numerics follow from them. Use for: the bridge from FDTD theory to Meep's specific conventions, right before writing the Meep-comparison notebook (spec §11, I2).
- [Docs: Meep — "Units and Nonlinearity"](https://meep.readthedocs.io/en/latest/Units_and_Nonlinearity/)
  Meep's own page on its dimensionless/normalized unit system (c = ε₀ = μ₀ = 1) — the same convention waveyard's spec adopts (§15, D11). Use for: understanding *why* Meep (and this project) express fields and cell sizes in normalized units before comparing runs.

### 2. How existing simulators structure their code

- [Repo: Meep (NanoComp/meep)](https://github.com/NanoComp/meep) — **RECOMMENDED READ for the structure/fields split specifically**
  C++ core (`src/`) with Python/Scheme bindings. Its own docs ([Chunks and Symmetry](https://meep.readthedocs.io/en/latest/Chunks_and_Symmetry/)) and headers (`src/meep.hpp`, `structure.cpp`, `fields.cpp`) show a hard split between an immutable, chunk-decomposed `structure` (geometry/materials — doesn't change during a run) and a `fields` object owning all mutable time-stepped state. One-line lesson: **separate the static description of a simulation from its mutable time-evolving state, so one `structure` can drive multiple `fields` runs.**
- [Repo: Tidy3D Python client (flexcompute/tidy3d)](https://github.com/flexcompute/tidy3d)
  This is the open-source *client* (not the solver, which runs on Flexcompute's servers). Core classes live under `tidy3d/components/`: `simulation.py` (`Simulation`), `structure.py` (`Structure`), `medium.py` (media), `source.py` (sources), `monitor.py` (monitors) — all subclassing one pydantic base, `Tidy3dBaseModel`, in `base.py`. One-line lesson: **the whole simulation spec can be a validated tree of pydantic models, so validation, serialization, and the API surface all fall out of the schema itself** — the same approach waveyard's spec already commits to (§8, "all classes are pydantic v2 `BaseModel` with `frozen=True`").
- [Paper: Mahlau et al., "A flexible framework for large-scale FDTD simulations: open-source inverse design for 3D nanostructures," arXiv:2412.12360](https://arxiv.org/abs/2412.12360) and [Repo: ymahlau/fdtdx](https://github.com/ymahlau/fdtdx)
  JAX-based, reverse-mode-autodiff FDTD exploiting time-reversal of Maxwell's equations to cut memory; scales to multi-GPU and millions of design parameters (already cited in spec §17). One-line lesson: **a JAX/functional design threads state through pure step functions instead of mutating objects, which is what buys free autodiff through the whole simulation** — directly relevant since waveyard's own `Plan`/`State` are already plain (frozen) dataclasses of arrays, not stateful objects (spec §8.4).
- [Repo: flaport/fdtd](https://github.com/flaport/fdtd) — **RECOMMENDED READ overall for this topic**
  A complete, small (~12 files), readable 3D Yee-grid FDTD in NumPy with optional PyTorch/CUDA backends. Package layout: `grid.py`, `boundaries.py`, `sources.py`, `detectors.py`, `objects.py`, `backend.py`. One-line lesson: **the whole FDTD problem decomposes into a handful of orthogonal concepts — Grid, Boundaries, Sources, Detectors, and a swappable numeric Backend** — small enough to read end to end in an afternoon, with none of Meep's build complexity or Tidy3D's 8000-line simulation.py.
- [Repo: fancompute/ceviche](https://github.com/fancompute/ceviche)
  Differentiable FDFD/FDTD from the Stanford Fan group (Tyler Hughes et al.), made autodiff-capable by writing an otherwise ordinary NumPy/SciPy solver against `autograd`. One-line lesson: **autodiff-compatibility can be a thin "which array library you compute with" layer choice, rather than a full architectural redesign** — the opposite lesson from fdtdx, worth reading as a contrast pair.

  Suggested reading order for this topic: flaport/fdtd first (minimal architecture) → Meep's structure/fields split (how it scales to a production C++ engine) → Tidy3D's pydantic component tree (how to expose it as a validated user-facing API) → fdtdx and ceviche (two different ways to bolt on autodiff).

### 3. Python idioms the spec relies on

- [Docs: Pydantic v2 — "Models"](https://docs.pydantic.dev/latest/concepts/models/) — **RECOMMENDED READ for this topic**
  Note: this URL 301-redirects to `https://pydantic.dev/docs/validation/latest/concepts/models/`; both resolve as of today, the old `docs.pydantic.dev` path is given here since it's the one likely to stay memorable/linked elsewhere. Defines `BaseModel`, fields, and `model_config`. Use for: the base of every object-model class in `model/`. Frozen models are documented on this *same* page under "Faux immutability" (anchor `#faux-immutability`) — it explains that `frozen=True` emulates immutability (mutation raises a `ValidationError` of type `frozen_instance`), which matters given the spec requires `frozen=True` everywhere (§8).
- [Docs: Pydantic v2 — "Validators"](https://docs.pydantic.dev/latest/concepts/validators/)
  Covers `@field_validator` and `@model_validator` (before/after/wrap/plain modes). Use for: the stability checks the spec requires (e.g. the Lorentz-pole ω_pΔt/δ_pΔt guards in §Validation, `Simulation.validate()`).
- [Spec: Python array API standard, v2025.12](https://data-apis.org/array-api/latest/)
  The standard itself (Consortium for Python Data API Standards), not a library — already cited in spec §17. Use for: writing the functional stepper (spec §8.4, G5) against a portable array interface instead of NumPy or PyTorch directly.
- [Docs/Repo: array-api-compat](https://data-apis.org/array-api-compat/) ([github.com/data-apis/array-api-compat](https://github.com/data-apis/array-api-compat))
  The compatibility shim that lets NumPy/PyTorch/CuPy code actually target the array API standard above. Use for: the one place `numpy`/`torch` get imported behind a portable interface in the `backends/` layer.
- [Docs: Python 3 — `typing.Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)
  Official language reference for structural subtyping and `@runtime_checkable`. Use for: the `Backend` protocol (spec §8.4) that both NumPy and PyTorch backends satisfy without inheriting from a common base class.
- [Docs: Python 3 — `dataclasses`, "Frozen instances"](https://docs.python.org/3/library/dataclasses.html#frozen-instances)
  Official docs for `@dataclass(frozen=True)` — covers the `__setattr__`/`__delattr__` override and `FrozenInstanceError`. Use for: `Plan` and `State` (spec §8.4), which are explicitly plain frozen dataclasses of arrays, distinct from the pydantic object model.
- [Docs: uv — "Working on projects"](https://docs.astral.sh/uv/guides/projects/)
  The practical day-to-day workflow page (`uv init`, `pyproject.toml`/`uv.lock`, `uv add`/`uv run`/`uv build`), not just the marketing homepage. Use for: day-one repo setup (README's `uv sync --extra dev`).
- [Docs: Ruff — "Rules"](https://docs.astral.sh/ruff/rules/)
  Full reference of lint rules with the default-enabled set (F, E, B, UP, RUF) and fixability markers. Use for: configuring lint + format (spec §12, "Quality").
- [Docs: mypy — "Getting started"](https://mypy.readthedocs.io/en/stable/getting_started.html)
  Canonical on-ramp: function annotations, the `typing` module, stub files. Use for: getting `mypy --strict` passing on `model/`, `plan/`, `backends/` (spec §12) before reaching for `Protocol`-based narrowing specifically.
- [Docs: xarray — "Data Structures"](https://docs.xarray.dev/en/stable/user-guide/data-structures.html)
  Covers `DataArray`/`Dataset`/coordinates. Use for: the S-parameter and field-monitor outputs the spec already commits to exporting as xarray with physical coordinates in µm (spec §G4, §Field monitor).

## Wisdom (Communities)

- [Meep — GitHub Discussions](https://github.com/NanoComp/meep/discussions)
  The current, active venue (Q&A/General/Show-and-tell categories, live threads through September 2026) — this is where Meep's own maintainers point users today. Use for: Meep-specific numerics questions and the Meep-comparison notebook (spec I2–I4). Note: the older `meep-discuss` mailing list is dead (archive only, postings 2006–2021) — don't post there.
- [gdsfactory — GitHub Discussions](https://github.com/gdsfactory/gdsfactory/discussions)
  Primary community hub per the gdsfactory README. Use for: layout/`LayerStack`/gplugins questions when wiring up `Simulation.from_component`. A Slack community also exists (invite link found in gdsfactory's docs) but Slack invite links rotate/expire, so GitHub Discussions is the more durable pointer to give here.

## Gaps / verification notes

- **Taflove & Hagness's official Artech House product pages returned HTTP 403** on direct fetch (both the US and UK storefronts) — likely bot-blocking on their storefront, not necessarily that the pages are gone. The Google Books page above was independently verified and used as the stable citation instead; a WorldCat redirect (`search.worldcat.org/isbn/9781580538329`) also resolves but its content could not be extracted, so it's not relied on here.
- **No single Meep doc page is literally titled "The Meep FDTD Algorithm."** The closest and most accurate primary source is the "Finite-Difference Time-Domain Methods" section of the Introduction page (linked above); a companion page, `Yee_Lattice`, covers the Yee-lattice detail specifically and is worth a follow-up read but was not independently re-fetched during this pass.
- **fdtdx's "functional, no mutable OO state" characterization is inferred from JAX's inherent design and the paper's own description of reverse-mode autodiff/time-reversibility**, not from a literal quote in the repo's README — the module layout (`objects/`, `core/`, `fdtd/`) doesn't by itself rule out some object-oriented organization around the functional JAX core. Worth confirming by reading `src/fdtdx/fdtd/` directly before teaching this as settled fact.
- **gdsfactory's Slack invite link** (`join.slack.com/t/gdsfactory-community/shared_invite/...`) was seen in gdsfactory's docs but such links expire/rotate; verify it resolves before handing it to the owner, and prefer the GitHub Discussions link as the durable default.
