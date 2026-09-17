# waveyard

Learning-first FDTD simulator for photonic integrated circuits. The owner
writes the numerical core and the architecture; agents scaffold, test,
review, and teach. Read `docs/spec/v0.1.md` for the full design and the
wayfinder map (issue labelled `wayfinder:map`) for what is decided.

## Agent skills

- Issue tracker: GitHub Issues on this repo. See `docs/agents/issue-tracker.md`.
- Domain docs: single context. Glossary at `CONTEXT.md` (created when the
  first term is settled); decisions in `docs/adr/`.
- Teaching workspace: `learning/` (git-ignored) holds `MISSION.md`,
  `lessons/`, `reference/`, `learning-records/` in the `teach` skill's format.

## Working agreements

- The owner writes the stepper, plan, and mode solver. Agents do not write
  those unless asked; they scaffold, write tests, and review.
- Introduce each library (pydantic, xarray, array-api-compat, torch) only at
  the milestone where it solves a felt problem, with a lesson first.
- Python 3.12 via `uv`. Meep lives in its own conda environment.
- Version control is a learning objective. The owner runs git and GitHub
  operations (branch, commit, push, PR, merge) with the agent explaining.
  Agents do not commit or push on the owner's behalf unless asked.
