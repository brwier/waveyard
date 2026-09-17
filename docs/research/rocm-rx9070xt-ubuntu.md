# ROCm + PyTorch version pins for an RX 9070 XT on Ubuntu 24.04

Research for issue #2. Investigated 2026-09-17 against AMD's own ROCm docs, the PyTorch
website, `download.pytorch.org`, and upstream GitHub issue trackers (ROCm, Triton, PyTorch,
ComfyUI, Ollama). All version numbers below were live at the time of research; ROCm was
shipping fast (weekly-to-monthly point releases) in 2026, so re-check the release-history
page before acting on this if it's more than a few weeks old.

## TL;DR — recommended pins

| Component | Pin | Why |
|---|---|---|
| OS | Ubuntu **24.04.4** (not .3 — EoS'd) | Required point release for gfx1201; see RDNA4 support status below |
| Kernel | Ubuntu 24.04 **GA 6.8** is sufficient for ROCm 7.2.x. If you instead track ROCm ≥ 10.0.0, you need the **HWE 6.17** kernel — GA 6.8 is not listed as supported there | [ROCm 7.2.1 system requirements](https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.1/reference/system-requirements.html), [ROCm 10.0.0 compatibility matrix](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html) |
| ROCm | **7.2.x line, latest patch = 7.2.4** (install method below); current AMD "latest" upstream is **10.0.0** (see caveat) | See "Does ROCm 7.2 exist / what's current stable" below |
| Install method | `amdgpu-install` package from `repo.radeon.com`, **not** plain `apt` from Ubuntu's own archive (Ubuntu's archive does not carry ROCm) | [ROCm 7.2.1 quick-start guide](https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.1/install/quick-start.html) |
| PyTorch wheel index | `https://download.pytorch.org/whl/rocm7.2` (official PyTorch-built wheels, includes `pytorch-triton-rocm`) | [PyTorch 2.9 wheel-variant-for-ROCm article, AMD Developer](https://www.amd.com/en/developer/resources/technical-articles/2025/pytorch-2-9-wheel-variant-support-expands-to-rocm.html); index confirmed live via direct fetch |
| Install command | `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm7.2` (or the `uv` equivalent, `uv pip install ... --index-url ...`) | same |
| Smoke test | `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name())"` (per spec §12; ROCm builds of PyTorch expose the GPU under the `cuda` device namespace) | project spec `docs/spec/v0.1.md` §12 |
| `HSA_OVERRIDE_GFX_VERSION` | **Not needed.** gfx1201 has had native kernels since ROCm 7.2; the override was only a workaround pre-7.2 | see RDNA4 caveats below |
| WSL2 | **Officially supported** since ROCm 7.2, Ubuntu 22.04/24.04 guest, needs Adrenalin 26.1.1-for-WSL2 on the Windows host | see WSL2 section |
| Native Windows PyTorch (no WSL2) | **Partially supported**: RX 9070/9070 XT (gfx1201) is on the Radeon-for-Windows hardware matrix for ROCm 7.2.1, but AMD's own docs say "the entire ROCm stack is not yet fully supported on Windows" | see native Windows section |

**Bottom line for the dual-boot decision:** dual-boot is **not required by a hard capability
gap** — ROCm 7.2+ works natively on Windows for this exact card, and WSL2 is also officially
supported as of ROCm 7.2. But both Windows paths carry the "not yet fully supported" /
comparatively immature caveat from AMD itself, and neither path had the breadth of
community mileage that native Ubuntu 24.04 + ROCm has. If the goal is a boring, reproducible
`torch.compile`/Triton-capable setup with the least friction, Ubuntu 24.04 native is still
the safer default; treat native-Windows or WSL2 as viable fallbacks, not equivalents, until
you've verified `torch.compile` and Triton stability there yourself.

---

## 1. Does "ROCm 7.2" exist, and what's current stable? (spec assumption check)

The v0.1 spec (`docs/spec/v0.1.md`, decision D9) assumes "ROCm 7.2 on RX 9000 (RDNA4)."

- **ROCm 7.2.0 exists and shipped 2026-01-21.** It's the release AMD documents as adding
  broadened RDNA4 desktop support (RX 9060 XT LP, R9600D) on top of the RDNA4 support that
  had already landed. Source: [ROCm 7.2.0 release notes](https://rocm.docs.amd.com/en/docs-7.2.0/about/release-notes.html), reported by [Phoronix](https://www.phoronix.com/news/AMD-ROCm-7.2-Released).
- The 7.2 line continued as a maintenance branch: **7.2.1** (2026-03-25, adds Ubuntu 24.04.4
  support and EoS's 24.04.3), **7.2.2** (~2026-04), **7.2.3** (2026-05-04), and **7.2.4**
  (packaging seen live at `repo.radeon.com/amdgpu-install/7.2.4/...`, no dated release-notes
  page found — **could not verify the exact 7.2.4 release date**). Source: [ROCm release history](https://rocm.docs.amd.com/en/docs-7.2.3/release/versions.html).
- **However, "ROCm 7.2" is not AMD's current stable as of 2026-09-17.** AMD's release
  cadence sped up mid-2026: the mainline moved to **7.14.0** (2026-07-15) and **7.14.1**
  (2026-09-02), then AMD changed its versioning scheme entirely and shipped **ROCm 10.0.0**
  on **2026-08-26**, which `rocm.docs.amd.com/en/latest/` now resolves to. Source: [ROCm release history (`/en/latest/release/versions.html`)](https://rocm.docs.amd.com/en/latest/release/versions.html), [ROCm 10.0.0 release notes](https://rocm.docs.amd.com/en/latest/about/release-notes.html).
  **Not fully verified:** whether 7.2.x and the 7.14→10.0 line are two parallel support
  channels (an LTS-style 7.2.x patch branch vs. a fast-moving mainline) or whether 7.2.x is
  simply superseded. AMD's docs did not state this explicitly anywhere I could fetch; treat
  this as an open question (see §6).
- **Recommendation:** pin the exact patch you install (e.g. `7.2.4`, verified via
  `apt show rocm-core` after install), not the bare "7.2" the spec wrote — write the real
  patch version into the README as spec §12 already asks for. If you want AMD's current
  upstream instead of the mature 7.2.x branch, that's ROCm **10.0.0**, but see the kernel
  and wheel-channel differences below before choosing it for a first setup.

## 2. RDNA4 / gfx1201 support status

- The RX 9070 XT (and RX 9070, RX 9070 GRE) map to LLVM target **gfx1201**, RDNA4. It is
  listed as officially supported hardware in the ROCm 7.2.1 system-requirements table and
  again in the ROCm 10.0.0 compatibility matrix. Sources: [ROCm 7.2.1 system requirements](https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.1/reference/system-requirements.html), [ROCm 10.0.0 compatibility matrix](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html).
- Under ROCm 7.2.1, RX 9070 XT's OS support is restricted to: **Ubuntu 24.04.4** (kernel
  6.8 GA or 6.17 HWE, either works), **Ubuntu 22.04.5** (kernel 5.15 GA or 6.8 HWE),
  **RHEL 10.1** (kernel 6.12.0-124), **RHEL 9.7** (kernel 5.14.0-611 minimum). Source: same
  system-requirements page as above (footnote on RDNA4 desktop cards).
- Under ROCm 10.0.0, the equivalent row narrows the Ubuntu 24.04 kernel choice to **HWE
  6.17 only** (GA 6.8 not listed for that release), and adds Ubuntu 26.04 (GA 7.0) as an
  option. Source: [ROCm 10.0.0 compatibility matrix](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html).
- PyTorch's official ROCm wheel builds (`download.pytorch.org/whl/rocm7.2`) target
  gfx90a, gfx940/941/942, gfx950, gfx1100/1101/1102 (RDNA3), and **gfx1200/gfx1201**
  (RDNA4) — confirmed by AMD's own developer article on wheel-variant support. Source:
  [PyTorch 2.9 wheel-variant support expands to ROCm](https://www.amd.com/en/developer/resources/technical-articles/2025/pytorch-2-9-wheel-variant-support-expands-to-rocm.html).
  The index itself was reachable and lists `torch`, `torchvision`, `torchaudio`, and
  `pytorch-triton-rocm` packages (fetched directly 2026-09-17), confirming Triton ships in
  this channel.
- AMD's newer packaging (`stable.repo.amd.com/rocm/whl-next/`, used for ROCm ≥ 10.0.0)
  uses a device-tagged extra, e.g. `torch[device-gfx1201]==2.13.0+rocm10.0.0`, rather than
  a single generic ROCm-version index. This is a different install shape than the
  `download.pytorch.org` channel and is newer/less battle-tested. Source: [ROCm AI Ecosystem — Install PyTorch for ROCm](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html).

## 3. Caveats

- **`HSA_OVERRIDE_GFX_VERSION`:** not required for gfx1201 on ROCm ≥ 7.2 — native kernels
  exist. Historically (pre-7.2, and in ROCm-adjacent tools like older Ollama ROCm builds),
  people overrode gfx1201 to report as a supported architecture like gfx1100 or gfx1030 to
  get *any* kernel dispatch; this is a workaround for unsupported cards, not something the
  RX 9070 XT needs on a current ROCm. Source: general behavior documented in [ollama/ollama #10033](https://github.com/ollama/ollama/issues/10033) and [mudler/LocalAI #5822](https://github.com/mudler/LocalAI/issues/5822) (both about *other*, still-unsupported gfx targets needing the override — evidence for what the override is for, not evidence RX 9070 XT needs it).
- **Kernel floor:** see table above — ROCm 7.2.x is fine on Ubuntu 24.04's GA 6.8 kernel;
  ROCm ≥ 10.0.0 requires the HWE 6.17 kernel on Ubuntu 24.04. If you track upstream ROCm
  aggressively, budget for an HWE kernel upgrade. Source: [ROCm 10.0.0 compatibility matrix](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html).
- **Triton / `torch.compile` on gfx1201:** functional but with known rough edges as of
  2026-09:
  - A real Triton bug on RDNA4 (gfx1200/gfx1201): the AMD software-pipelining pass has a
    use-after-free when `num_stages >= 2`, causing crashes; reported against Triton 3.6.0
    via a downstream project (`sageattention` on ComfyUI) with the fix identified as a
    Triton-level num_stages issue. Source: [kijai/ComfyUI-WanVideoWrapper #2007](https://github.com/kijai/ComfyUI-WanVideoWrapper/issues/2007).
  - `gfx1201` was missing from AITER's (AMD's inference/training kernel library)
    architecture table, causing FP8 paths to silently fall back to FP32 instead of using
    native RDNA4 FP8 instructions. Not a `torch.compile`-blocking bug, but affects
    performance expectations if the project ever leans on FP8. Source: [ROCm/TransformerEngine #520](https://github.com/ROCm/TransformerEngine/issues/520).
  - Triton itself has an open architecture-specific correctness issue for OCP FP8
    (e4m3fn) on gfx12 (RDNA4): upcasts fall to a software path instead of using the
    native `v_cvt_pk_f32_fp8` instruction. Source: [triton-lang/triton #11497](https://github.com/triton-lang/triton/issues/11497).
  - General assessment from the vLLM/sglang RDNA4-enablement threads: base Triton kernel
    execution on RDNA3/4 works and doesn't require Triton compiler fixes for the common
    path — the open issues are specific ops/dtypes (FP8) and pipelining depth, not "Triton
    doesn't run on gfx1201." Source: [sgl-project/sglang #30599](https://github.com/sgl-project/sglang/issues/30599).
  - **Practical guidance for this project:** the FDTD stepper in the spec is fp32-only for
    v1 (D10), so the FP8-specific bugs above don't apply; the `num_stages` pipelining bug
    is the one to watch for if `compile=True` (spec D6/8.5) shows crashes — try
    `torch._inductor.config.triton.num_stages = 1` or disable `compile` if that happens.
    **Not independently verified against this exact stepper** — flag as a risk to check
    during M5 (GPU + Meep milestone in the spec's schedule), not a confirmed blocker.
- **Containers:** vLLM (a different, unrelated project) reported RDNA4-in-container
  failures around `amdgpu-smi` and `torch.cuda.device_count()` — a signal that container
  GPU passthrough on gfx1201 is another spot with known rough edges, relevant if this
  project's CI or dev environment considers Docker-based ROCm. Source: [vllm-project/vllm #40081](https://github.com/vllm-project/vllm/issues/40081).

## 4. WSL2 status

- ROCm's WSL2 support matrix (Radeon/Ryzen docs) lists, for **ROCm 7.2.1**: Radeon Software
  for Windows = **Adrenalin Edition 26.1.1 for WSL2**, Linux guest = **Ubuntu 24.04.2
  Desktop with HWE** (also Ubuntu 22.04 with WSL2-Linux-Kernel 5.15), supported hardware
  including **AMD Radeon RX 9070 XT**. Source: [WSL support matrices by ROCm version](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/wsl/wsl_compatibility.html).
  This is a real, dated, first-party support claim — not a community workaround.
- A live community report (a GitHub issue on `ROCm/librocdxg`, filed against a slightly
  different Ubuntu WSL guest version, 26.04) describes gfx1201/RDNA4 "working via
  librocdxg on WSL2" — consistent with, but not the same primary claim as, AMD's own
  matrix. Source: [ROCm/librocdxg #74](https://github.com/ROCm/librocdxg/issues/74) (community report, not AMD documentation — treated as corroboration, not primary evidence).
- **Not verified:** whether `torch.compile`/Triton has the same reliability under WSL2 as
  under native Linux for this card — no primary source addressed this directly; the docs
  above cover driver/runtime support, not compiler-stack parity.

## 5. Native Windows status (no WSL2)

- AMD's Radeon/Ryzen Windows compatibility matrix lists, for **ROCm 7.2.1**: supported
  architectures **gfx1201, gfx1200, gfx1100, gfx1101**, supported hardware including
  **AMD Radeon RX 9070** and **AMD Radeon RX 9070 XT**. Source: [Windows support matrices by ROCm version](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/windows/windows_compatibility.html).
- The same page carries an explicit AMD caveat (footnote on the 7.2.1 row): **"PyTorch on
  Windows includes ROCm 7.2.1 components; however, the entire ROCm stack is not yet fully
  supported on Windows."** This is the load-bearing sentence for the dual-boot decision —
  AMD itself is saying native-Windows ROCm/PyTorch is real but partial, not "equivalent to
  Linux." Source: same page.
- Native Windows install commands do exist and are documented: `pip install` against
  wheels hosted at `repo.radeon.com/rocm/windows/rocm-rel-7.2.1/...` (e.g.
  `torch-2.9.1+rocm7.2.1-cp312-cp312-win_amd64.whl`). Source: [ROCm — Install PyTorch via PIP (native Windows)](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installrad/windows/install-pytorch.html).
  That page's example output referenced `gfx1201` in the context of a different card (AMD
  Radeon AI PRO R9700) rather than showing RX 9070 XT explicitly in the worked example —
  **could not fully verify** the RX 9070 XT is exercised in AMD's own worked example, only
  that it's on the supported-hardware list on the compatibility-matrix page above.
- A live counter-example worth flagging: Ollama (a different project) reported the ROCm
  backend failing to initialize on the closely related gfx1201 card "AMD Radeon AI PRO
  R9700" under Windows 11, i.e. native-Windows gfx1201 initialization issues have been seen
  in the wild outside AMD's own smoke tests. Source: [ollama/ollama #14686](https://github.com/ollama/ollama/issues/14686) (third-party tool, not evidence of a PyTorch-specific bug, but a relevant risk signal).

## 6. Open uncertainties (things I could not verify)

- Whether the ROCm 7.2.x maintenance branch and the 7.14.x→10.0.0 mainline are officially
  two parallel supported channels, or whether 7.2.x is simply an older line users should
  move off of. AMD's docs I could reach didn't state a policy on this either way.
- The exact release date of ROCm **7.2.4** (the amdgpu-install package was live at
  `repo.radeon.com/amdgpu-install/7.2.4/...`, but no dated release-notes page was found for
  it in this research pass).
- Whether `torch.compile` + Triton is stable end-to-end on gfx1201 for a workload shaped
  like this project's FDTD stepper specifically — the Triton/AITER issues found are from
  unrelated projects (ComfyUI, vLLM, sglang, TransformerEngine) using different op mixes
  (attention kernels, FP8 GEMMs), not a stencil-update kernel. Treat the D6/8.5 `compile=True`
  target in the spec as unverified until M5's own benchmark is run.
- Whether `torch.compile`/Triton reliability on WSL2 matches native Linux — no primary
  source directly compared the two for this GPU.
- Whether the RX 9070 XT is used in AMD's own native-Windows PyTorch worked example (vs.
  only appearing on the separate supported-hardware list).

## Sources consulted

- ROCm 7.2.1 system requirements: https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.1/reference/system-requirements.html
- ROCm 7.2.1 quick-start install guide: https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.1/install/quick-start.html
- ROCm 7.2.1 PyTorch install page: https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.1/install/3rd-party/pytorch-install.html
- ROCm 7.2.0 release notes: https://rocm.docs.amd.com/en/docs-7.2.0/about/release-notes.html
- ROCm release history (7.2.x through 7.2.3): https://rocm.docs.amd.com/en/docs-7.2.3/release/versions.html
- ROCm release history (current/latest): https://rocm.docs.amd.com/en/latest/release/versions.html
- ROCm 10.0.0 release notes: https://rocm.docs.amd.com/en/latest/about/release-notes.html
- ROCm 10.0.0 compatibility matrix: https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html
- ROCm AI Ecosystem — Install PyTorch for ROCm (current): https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html
- WSL support matrices by ROCm version: https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/wsl/wsl_compatibility.html
- Windows support matrices by ROCm version: https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/windows/windows_compatibility.html
- Native Windows PyTorch install (pip): https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installrad/windows/install-pytorch.html
- AMD Developer — PyTorch 2.9 wheel-variant support expands to ROCm: https://www.amd.com/en/developer/resources/technical-articles/2025/pytorch-2-9-wheel-variant-support-expands-to-rocm.html
- PyTorch wheel index (fetched directly): https://download.pytorch.org/whl/rocm7.2
- Phoronix — AMD ROCm 7.2 released: https://www.phoronix.com/news/AMD-ROCm-7.2-Released
- triton-lang/triton #11497 (gfx12 FP8 upcast): https://github.com/triton-lang/triton/issues/11497
- kijai/ComfyUI-WanVideoWrapper #2007 (Triton num_stages bug on RDNA4): https://github.com/kijai/ComfyUI-WanVideoWrapper/issues/2007
- ROCm/TransformerEngine #520 (gfx1201 missing from AITER arch table): https://github.com/ROCm/TransformerEngine/issues/520
- sgl-project/sglang #30599 (RDNA3/4 enablement tracking): https://github.com/sgl-project/sglang/issues/30599
- vllm-project/vllm #40081 (RDNA4-in-container issues): https://github.com/vllm-project/vllm/issues/40081
- ollama/ollama #14686 (gfx1201 init failure on native Windows, different card): https://github.com/ollama/ollama/issues/14686
- ollama/ollama #10033 and mudler/LocalAI #5822 (general `HSA_OVERRIDE_GFX_VERSION` usage): https://github.com/ollama/ollama/issues/10033, https://github.com/mudler/LocalAI/issues/5822
- ROCm/librocdxg #74 (community WSL2 gfx1201 report): https://github.com/ROCm/librocdxg/issues/74
