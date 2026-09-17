# Handoff: bootstrap the desktop and do the AFK work

This document has two readers. The first section is a checklist for the
owner at a bare Ubuntu 24.04 install (the desktop: Ryzen 7 5700X3D, 32 GB,
RX 9070 XT). Everything after it is for the Claude Code session the owner
starts at the end of that checklist. Written 2026-09-17 by the laptop
session that surveyed the wayfinder map.

## Before the session exists (owner, at the desktop)

The setup wizard lives in this repo, so the repo is cloned by hand first.
The wizard installs ROCm, uv, Python 3.12, and PyTorch for ROCm, reboots up
to three times, and skips finished stages on each rerun.

1. Base tools:
   ```sh
   sudo apt update && sudo apt install -y git gh curl
   ```
2. Clone to the path the wizard expects:
   ```sh
   git clone https://github.com/brwier/waveyard.git ~/projects/waveyard
   ```
3. Run the wizard. After each reboot, log in and run it again until it
   prints the PyTorch smoke test and a block of facts:
   ```sh
   bash ~/projects/waveyard/scripts/desktop-rocm-setup.sh
   ```
   It writes those facts to `~/.waveyard-desktop.env`. The session resolves
   the dual-boot ticket from that file, so no need to paste anything.
4. Sign in to GitHub: `gh auth login` (HTTPS, browser).
5. Install Claude Code and sign in:
   ```sh
   curl -fsSL https://claude.ai/install.sh | bash
   cd ~/projects/waveyard && claude
   ```
6. Inside Claude Code, install the skills plugin:
   `/plugin install mattpocock-skills@claude-plugins-official`
7. First prompt: "Read docs/agents/handoff-desktop.md and carry it out. I am
   leaving now." Then leave.

## For the session

Read `CLAUDE.md` first; its working agreements bind you. The map is issue #1
(`gh issue view 1`), the spec is `docs/spec/v0.1.md`, and the tracker
conventions are in `docs/agents/issue-tracker.md`. The owner is away; work
through every stage below and stop only for the report.

## Authorizations for this handoff

The owner runs git and GitHub as a learning objective. For this unattended
run the owner grants the following, and only the following. Strike lines
you did not grant, owner.

- Commit on branches named `agent/<stage>` and `prototype/<name>`. Push
  them. Never commit to `main`.
- Open no pull requests and merge nothing. The owner reviews each branch
  and merges it as a git lesson.
- Create and comment on issues per the wayfinder conventions. Close only
  tickets whose type is `research` or `task`. Grilling and prototype
  tickets stay open for the owner's half.
- Every commit ends with the attribution lines your session reminder gives.

## Stage 0: verify the machine and resolve the dual-boot ticket

The owner ran `scripts/desktop-rocm-setup.sh` before starting you. Verify
its work, and repair anything that fails:

```sh
gh auth status
uv --version && uv python find 3.12
rocminfo | grep -m1 gfx
uv run --no-project python -c "import torch; print(torch.version.hip, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
cat ~/.waveyard-desktop.env
```

The wizard installs torch into `.venv` from the ROCm index with `uv pip`,
outside the project's lockfile. Any later `uv sync` prunes it. After Stage
1, reinstall it and rerun the check:

```sh
uv pip install torch --index-url https://download.pytorch.org/whl/rocm7.2
```

If ROCm or the GPU check fails, record the exact output in your final
report and continue with CPU-only work. Everything below runs on CPU.

Confirm the `Skill` tool lists `teach`, `wayfinder`, `prototype`,
`research`, `grilling`, and `domain-modeling`. If any is missing, the
plugin install in the owner's checklist failed; put that in the report and
carry on with the stages that need no skill.

When the GPU check passes, resolve the task ticket "Dual-boot Ubuntu 24.04
on the desktop for ROCm" (#9): comment with the contents of
`~/.waveyard-desktop.env` as the resolution, close it, and append one line
to the map's Decisions so far with the ROCm version, kernel, and torch
version from that file. If the check fails, comment on the ticket with the
failure output and leave it open.

Stage done when every command above prints sane output and ticket #9 is
either closed or carries the failure comment.

## Stage 1: project scaffolding (branch `agent/scaffolding`)

The closed ticket "Python and dependency compatibility for the laptop
environment" (#4) settled the packaging. Its findings live on the unmerged
branch `research/python-deps` at `docs/research/python-deps.md`; read that
file from the branch with `git show research/python-deps:docs/research/python-deps.md`.
Apply its recommended `pyproject.toml` block verbatim: the `<3.15` ceiling,
the `core`/`gds`/`torch`/`wgpu`/`dev` extras, the CPU torch index under
`[tool.uv]`. Then add:

- `[tool.ruff]`, `[tool.mypy]` (strict on `src/`), and `[tool.pytest.ini_options]`
  registering the spec §11 markers: `unit`, `analytic`, `integration`,
  `parity`, `meep`, `gpu`, `slow`, `bench`.
- `tests/test_import.py`: one `unit` test that imports `waveyard`.
- `.github/workflows/ci.yml`: on push and pull request, `uv sync --extra
  core --extra dev`, then ruff, mypy, pytest, on Python 3.12 only.
- A `Development` section in `README.md` with the two install commands from
  the findings doc, replacing the current stub, plus one line saying the
  desktop installs torch from the ROCm index with `uv pip` after every
  `uv sync`, as in Stage 0.

Stage done when, from a clean checkout of the branch:

```sh
uv sync --extra core --extra dev && uv run ruff check . && uv run mypy src && uv run pytest -m unit
```

exits 0, and the workflow file passes `actionlint` if available.

## Stage 2: the three-layer prototype (ticket #7, branch `prototype/three-layer-1d`)

Claim the ticket (`gh issue edit 7 --add-assignee @me`). Load the
`prototype` skill and read the ticket body; it is the whole brief. Build
`prototypes/three_layer_1d.py`: a few dozen lines, NumPy only, a tiny
`Simulation` description, a `Plan` of plain arrays, a pure `step(state,
plan, n) -> state`, a Gaussian point source, a time monitor, a simple PML.
Physics reference for the 1D update and PML: Schneider's free book, chapters
3 and 11, linked from `docs/research/curriculum-sources.md`.

Write `prototypes/README.md` with the four questions from the ticket body,
and under each, what the prototype *shows*: where each piece of state lives,
what crosses the plan boundary, the allocation cost of the functional style
at this size (measure it: steps per second with and without copying).
State observations, leave the verdicts to the owner.

Post a comment on the ticket with the branch name and a one-paragraph
summary of the observations. Leave the ticket open and assigned to you; the
owner resolves it after reacting.

Stage done when `uv run python prototypes/three_layer_1d.py` runs in under
five seconds on CPU and writes a PNG of the pulse hitting the PML, and the
README answers all four questions with evidence.

## Stage 3: teaching workspace foundations (no branch; see the note)

`learning/` is git-ignored, so this stage lives only on this machine. Say
so in your report so the owner can un-ignore it or copy it.

Load the `teach` skill. Create, in `learning/`:

- `RESOURCES.md` in the skill's RESOURCES format, built from
  `docs/research/curriculum-sources.md`. Keep its Knowledge, Wisdom, and
  Gaps sections; drop nothing the research verified.
- `assets/style.css`: the shared stylesheet every lesson links. Readable
  typography, prints well, light and dark.
- `assets/quiz.js`: a quiz component with immediate feedback and equal-length
  answer options, per the skill's quiz rule.
- `assets/code-block.css` or equivalent for Python listings with line numbers.
- `lessons/0000-template.html`: a lesson skeleton linking the assets, with
  the primary-source slot and the ask-your-teacher reminder the skill
  requires.

Write no `MISSION.md` and no numbered lesson; both need the owner. Write no
`learning-records/`; nothing has been learned yet.

Stage done when the template opens in a browser, renders one quiz question
with feedback, and `RESOURCES.md` lists every source the research doc
verified.

## Stage 4: Meep environment (new research ticket, branch `agent/meep-env`)

The map's fog lists "Meep environment: conda lockfile, which Meep version,
2D-first comparison setup". Graduate it: create a child issue of the map,
label `wayfinder:research`, title "Meep environment: conda spec, version
pin, 2D smoke test", claim it, and remove that line from the map's Not yet
specified section.

Install Miniforge if `conda` is absent. Create `envs/meep.yml` pinning
`pymeep` from conda-forge on Python 3.13 or lower (the findings doc records
that no 3.14 build exists). Produce a lockfile with `conda-lock` if it
installs cleanly, else record the exact resolved versions with `conda list
--explicit`. Add `envs/meep_smoke_2d.py`: a 2D straight waveguide, one
`EigenModeSource`, one flux monitor, runs in under a minute.

Write `docs/research/meep-environment.md`: what was pinned, why, how long
the smoke test takes, and the exact commands to recreate the environment.
Resolve the ticket per `docs/agents/issue-tracker.md`: comment, close, and
append one line to the map's Decisions so far.

Stage done when `conda run -n waveyard-meep python envs/meep_smoke_2d.py`
prints a flux value and the ticket is closed with the map updated.

## Stage 5: validation triage proposal (branch `agent/validation-triage`)

The fog lists "which of the spec's validation tests (§11) survive the
learning re-cut, and in what order they are earned by the reordered
milestones". The decision is the owner's; the analysis is yours.

Write `docs/research/validation-triage.md`: a table of every test in spec
§11 (unit, A1–A8, M1–M4, I1–I5, P1–P4) with a proposed milestone under the
stepper-first order recorded in the map's Notes (1D stepper with pulse and
PML, then 2D, then mode solver, geometry, ports, GPU), and a keep/defer/drop
recommendation with one line of reasoning each. Then create a child issue of
the map, label `wayfinder:grilling`, title "Validation tests: which survive
the re-cut and when each is earned", body pointing at the doc, blocked by
"Milestone and lesson sequence for spec v0.2" (#6) using the native
dependency call in the tracker doc. Remove the fog line from the map.

Stage done when every §11 test appears in the table exactly once and the
ticket exists with its blocking edge visible on GitHub.

## Stage 6: seed the glossary (branch `agent/context-seed`)

Load the `domain-modeling` skill and create `CONTEXT.md` in its
CONTEXT format with the six terms the map names: Structure, Plan, Port,
Monitor, Backend, State. Definitions come from spec §8 and §9 only, stated
as what each thing *is* in the domain, free of implementation detail.
Remove the fog line "Seeding CONTEXT.md with the spec's vocabulary" from
the map and add one line to Not yet specified: "Challenge the seeded
glossary against the prototype's boundaries once the owner has reacted to
it."

Stage done when all six terms are defined and the map's fog reflects the
change.

## Stage 7: report

Post one comment on the map issue titled "Desktop bootstrap report" listing:
each stage with done or blocked, every branch pushed with what to review on
it, the exact output of any failed check from Stage 0, and the note that
`learning/` exists only on this machine. Repeat that comment as your final
message.

## Order and parallelism

Stages 0 and 1 first, in order. Stages 2 through 6 are independent of each
other; run 2 next because two grilling tickets are blocked on it. If a stage
blocks, record why in the report and move on. Nothing in Stages 2 through 6
depends on the GPU.
