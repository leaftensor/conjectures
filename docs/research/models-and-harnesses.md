# Automated Lean 4 Theorem Proving and Counterexample Search: 2026 State of the Art

A research appendix for someone who has to pick a stack and run it against the
`conjectures.io` target pool (Bittensor Subnet 66).

**Scope and rules of evidence.** Every number below is one I read on a page that is
linked inline. Where a paper, a model card, and a repo README disagree, I report the
disagreement rather than picking a winner. Where I could not verify something, it is
marked `UNVERIFIED:` with a statement of what I could not confirm. I separate what a
system's authors *claim* from what has been *independently checked*; where a result has
a third-party Lean verification I say so, and where it is only an announced preprint or
a posted chat log I say that instead.

For orientation, the target pool itself. **Read from the pinned checkout and the live
catalogue, which agree with each other and not with the rendered GitHub page:**

| Source | Says |
|---|---|
| `conjectures-tasks/README.md` at the pinned commit `8432eac9` | **518 bundles** — proof/refutation pairs for **259** audited direct propositions (235 Erdős, 24 Green's) |
| `GET https://conjectures.io/v1/catalog/conjectures` (14 Sept 2026) | **260** conjectures — 236 Erdős, 24 Green's; 253 with a payable bounty |
| `GET https://conjectures.io/v1/catalog/meta` | `conjectures: 260`, `open_targets: 253`, `credit_price_rao: 250000000` |
| The rendered `github.com/conjectures-io/conjectures-tasks` page | **418 bundles / 209 propositions (189 Erdős, 20 Green's)** — a stale render of an older commit |
| `https://conjectures.io/status` | pinned revision **`379fc0298dc1`** — stale; the live API and validator both serve `8432eac9` |

So the working number is **259 in the pool, 260 listed**; the extra Erdős entry is
`Erdos10.erdos_10.variants.grechuk`, retired from the pool but still rendered with a
`SOLVED` badge. The 418/209 figures are an older snapshot and should not be planned against.
`UNVERIFIED:` why the GitHub page and the site's own `/status` page lag — I read the
discrepancy but not an explanation for it.

The live toolchain, from `/v1/catalog/meta`: Lean `leanprover/lean4:v4.27.0`, Mathlib
`a3a10db0e9d6`, Formal Conjectures `8432eac998110a563e03df65a28c117e97c8c142`, Comparator
`68a064109f01`, nanoda `f58f2f6d535e` (both kernels disabled on the tasks sampled —
`enable_nanoda: false`).

---

## 1. Dedicated neural provers

### 1.1 The comparison table

All miniF2F numbers are **miniF2F-test**. Read the budget column before comparing
anything: pass@32 and pass@8192 are different products, not different quality levels.
"Self-correction" / "w/ sc" means the model is fed Lean compiler errors and revises.

| Model | Params | miniF2F-test | PutnamBench | Weights | License |
|---|---|---|---|---|---|
| Goedel-Prover-SFT (V1) | 7B | 57.6% @32; 62.7% @3200; 64.7% @25600 ([repo](https://github.com/Goedel-LM/Goedel-Prover)) | 7 solved @512; 6 @32 ([repo](https://github.com/Goedel-LM/Goedel-Prover)) | [HF](https://huggingface.co/Goedel-LM/Goedel-Prover-SFT) | MIT ([repo](https://github.com/Goedel-LM/Goedel-Prover)) |
| Goedel-Prover-V2-8B | 8B | 84.6% @32; 87.9% @1024; 90.2% @8192; w/ sc 86.7% @32, 89.3% @1024 ([paper](https://arxiv.org/pdf/2508.03613)) | — | [HF](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-8B) | Apache-2.0 ([repo](https://github.com/Goedel-LM/Goedel-Prover-V2)) |
| Goedel-Prover-V2-32B | 32B | 88.1% @32; 90.4% w/ sc; 91.8% @1024; 92.2% @8192; w/ sc 92.6% @1024 ([paper](https://arxiv.org/pdf/2508.03613)) | 43 @32; 57 @32 w/ sc; 86 @184 w/ sc ([paper](https://arxiv.org/pdf/2508.03613)); card says 64 @64 ([HF](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-32B)) | [HF](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-32B) | Apache-2.0 |
| DeepSeek-Prover-V2-7B | 7B | 58.6% @1; 75.6% @32; 79.9% @1024; 82.0% @8192 (CoT) ([paper](https://arxiv.org/html/2504.21801)) | 8/658 @32; 11/658 @1024 (CoT) ([paper](https://arxiv.org/html/2504.21801)) | [HF](https://huggingface.co/deepseek-ai/DeepSeek-Prover-V2-7B) | MIT ([LICENSE](https://huggingface.co/deepseek-ai/DeepSeek-Prover-V2-7B/blame/main/LICENSE)) |
| DeepSeek-Prover-V2-671B | 671B MoE | 61.9% @1; 82.4% @32; 86.6% @1024; 88.9% @8192 ([paper](https://arxiv.org/html/2504.21801)) | 22/658 @32; 47/658 @1024 ([paper](https://arxiv.org/html/2504.21801)); README says 49 ([repo](https://github.com/deepseek-ai/DeepSeek-Prover-V2/blob/main/README.md)) | [HF](https://huggingface.co/deepseek-ai/DeepSeek-Prover-V2-671B) | MIT |
| Kimina-Prover-Preview-72B | 72B | 52.94% @1; 68.85% @32; 77.87% @1024; 80.74% @8192 ([paper](https://arxiv.org/html/2504.11354v1)) | — | not released | — |
| Kimina-Prover-72B | 72.7B | 63.9% @1; 84.0% @32; 87.7% @1024; 86.4% @32 +1 error-fix; 92.2% w/ TTRL ([blog](https://huggingface.co/blog/AI-MO/kimina-prover)) | — | [HF](https://huggingface.co/AI-MO/Kimina-Prover-72B) | MIT ([HF](https://huggingface.co/AI-MO/Kimina-Prover-72B)) |
| Kimina-Prover-Distill-1.7B | 1.7B | 72.95% @32 ([HF](https://huggingface.co/AI-MO/Kimina-Prover-Distill-1.7B)) | — | [HF](https://huggingface.co/AI-MO/Kimina-Prover-Distill-1.7B) | — |
| Kimina-Prover-RL-1.7B | 1.7B | 76.23% @32; 77.87% w/ error-fix ([blog](https://huggingface.co/blog/AI-MO/kimina-prover-rl)) | — | [HF](https://huggingface.co/AI-MO/Kimina-Prover-RL-1.7B) | — |
| Kimina-Prover-Distill-8B | 8B | 78.3% @32 ([blog](https://huggingface.co/blog/AI-MO/kimina-prover)) | — | [HF](https://huggingface.co/AI-MO/Kimina-Prover-Distill-8B) | — |
| Kimina-Prover-Preview-Distill-1.5B / 7B | 1.5B / 7B | 42.6% / 52.5% @1; 56.2% / 63.1% @32; 61.9% / 70.8% @1024 ([paper](https://arxiv.org/html/2504.11354v1)) | — | [HF](https://github.com/MoonshotAI/Kimina-Prover-Preview) | — |
| BFS-Prover | 7B | 70.83% ±0.89 @(2048×2×600); 72.95% accumulative ([paper](https://arxiv.org/html/2502.03438v2)) | — | — | — |
| InternLM2.5-StepProver | 7B | 59.4% BFS; 65.9% BFS+CG @(256×32×600) ([paper](https://openreview.net/pdf?id=qwCqeIg5iI)) | — | — | — |
| HunyuanProver | 7B | 64.8% BFS; 68.4% BFS+DC @(600×8×400) ([paper](https://arxiv.org/pdf/2412.20735)) | — | — | — |
| Leanabell-Prover (V1) | 7B | 59.8% @32 ([paper](https://arxiv.org/pdf/2504.06122v1)) | — | — | — |
| Leanabell-Prover-V2-DS / -KM | 7B | 78.2% / 70.4% @128; 76.6% / 68.4% @32 ([paper](https://arxiv.org/html/2507.08649v1)) | — | [GitHub](https://github.com/Leanabell-LM/Leanabell-Prover-V2) | — |
| OProver-32B | 32B | **93.3% @32** ([paper](https://arxiv.org/abs/2605.17283)) | 11.3% @32 ([paper](https://arxiv.org/abs/2605.17283)) | [HF collection](https://github.com/multimodal-art-projection/OProver) | — |
| OProver-8B | 8B | 91.8% @32 (from 79.5) ([secondary](https://eu.36kr.com/en/p/3845562669042179)) | — | [GitHub](https://github.com/multimodal-art-projection/OProver) | — |
| Pythagoras-Prover-32B | 32B | 89.8% @32; **93.03% @2048** ([paper](https://arxiv.org/pdf/2606.12594)) | 93/672 @64 ([paper](https://arxiv.org/pdf/2606.12594)) | — | — |
| Pythagoras-Prover-4B | 4B | 86.1% @32 ([paper](https://arxiv.org/pdf/2606.12594)) | — | — | — |
| Seed-Prover 1.0 | — | "almost solved"; 79% of previously formalized IMO problems ([ByteDance](https://seed.bytedance.com/en/blog/bytedance-seed-prover-achieves-silver-medal-score-in-imo-2025)) | — | not released | — |
| Seed-Prover 1.5 | — | — | 88% (580/660) ([paper](https://arxiv.org/abs/2512.17260)) | not released | — |

### 1.2 Reading the table honestly

**Pass@1 ≠ pass@32 ≠ pass@8192.** A 92.2% at pass@8192 for Kimina-Prover-72B came with
the TTRL search framework, and the same model is 63.9% at pass@1
([blog](https://huggingface.co/blog/AI-MO/kimina-prover)). DeepSeek-Prover-V2-671B at
pass@1 is 61.9%, so roughly half of its headline 88.9% is bought with sampling. For a
research-level target you are not sampling the same distribution as miniF2F anyway.

**Published numbers move between pages.** These are real, and they matter for
reproducibility:

- Goedel-Prover-V2-8B is **84.6% @32** in the paper and the 32B model card
  ([paper](https://arxiv.org/pdf/2508.03613),
  [card](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-32B)) but **83.0%** on the
  8B model card ([card](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-8B)).
- The 32B model card reports "88.0%" where the paper reports 88.1%, and reports
  PutnamBench **64 @ pass@64** where the paper reports **86 @ pass@192**
  ([card](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-32B),
  [paper](https://arxiv.org/pdf/2508.03613)).
- DeepSeek's own README says 49/658 PutnamBench where the paper says 47/658
  ([README](https://github.com/deepseek-ai/DeepSeek-Prover-V2/blob/main/README.md),
  [paper](https://arxiv.org/html/2504.21801)).
- Kimina's release blog headlines Kimina-Prover-RL-1.7B at 76.63% @32 in the prose and
  lists 76.23% in its own table ([blog](https://huggingface.co/blog/AI-MO/kimina-prover-rl)).

**Newer open-weight models.** OProver-32B claims 93.3% @32 on MiniF2F with open weights
and releases OProofs, a corpus of ~1.77M Lean statements and 6.86M compiler-verified
proofs ([paper](https://arxiv.org/abs/2605.17283),
[repo](https://github.com/multimodal-art-projection/OProver)). Pythagoras-Prover-32B
claims 93.03% @2048 and a 4B model that beats DeepSeek-Prover-V2-671B at matched pass@32
(82.4% → 86.1%) ([paper](https://arxiv.org/pdf/2606.12594)). Both postdate most leaderboard
snapshots; neither has the multi-party replication that miniF2F numbers usually get.
`UNVERIFIED:` I could not confirm the hardware, licence, or download location for
Pythagoras-Prover weights or for the Seed-Prover family — ByteDance's page describes
results but I found no weights release for either.

**Seed-Prover is not runnable by you.** Seed-Prover 1.0 solved 4 of 6 IMO 2025 problems
in-contest (5/6 counting a post-contest completion) across 3 days of attempts
([ByteDance](https://seed.bytedance.com/en/blog/bytedance-seed-prover-achieves-silver-medal-score-in-imo-2025),
[repo](https://github.com/ByteDance-Seed/Seed-Prover)). Seed-Prover 1.5 claims 88% of
PutnamBench, 80% of Fate-H, 33% of Fate-X and 11/12 Putnam 2025 problems in 9 hours, at
"10 H20 days per problem" ([paper](https://arxiv.org/abs/2512.17260)). It is a system
result, not a downloadable model.

### 1.3 Hardware, and why most of these numbers are irrelevant to a 1–8 GPU budget

VRAM below is **derived arithmetic**, not a cited figure: bf16 ≈ 2 bytes/parameter,
int8 ≈ 1, int4 ≈ 0.5, plus ~20% runtime overhead, weights only and batch 1. Compute it
yourself before you buy anything.

| Model | bf16 weights | 8-bit | 4-bit |
|---|---|---|---|
| Kimina-Prover-Distill/RL-1.7B | ~3.4 GB | ~2.1 GB | ~1.0 GB |
| DeepSeek-Prover-V2-7B | ~14 GB | ~8.4 GB | ~4.2 GB |
| Goedel-Prover-V2-8B | ~16 GB | ~9.6 GB | ~4.8 GB |
| Kimina-Prover-Distill-8B | ~16 GB | ~9.6 GB | ~4.8 GB |
| Goedel-Prover-V2-32B | ~64 GB | ~38 GB | ~19 GB |
| OProver-32B | ~64 GB | ~38 GB | ~19 GB |
| Kimina-Prover-72B | ~145 GB | ~87 GB | ~44 GB |
| DeepSeek-Prover-V2-671B | ~1342 GB | ~805 GB | ~403 GB |

Kimina-Prover-72B's own card recommends `tensor_parallel_size=8` and
`max_model_len=131072` ([HF](https://huggingface.co/AI-MO/Kimina-Prover-72B)), i.e. an
8-GPU node is the intended deployment. DeepSeek-Prover-V2-671B shares the DeepSeek-V3
architecture, for which the community reference points are ~16×H100-80GB for FP8, or
8×H200 / 8×B200 ([HF forum](https://discuss.huggingface.co/t/looking-for-a-multi-gpu-server-to-run-deepseek-prover-v2-671b-can-pay/177557/2)).
Both are out of reach for 1–8 GPUs; use the API or skip.

Add KV cache separately. For a Qwen2.5-72B-class GQA geometry (derived: 80 layers,
8 KV heads, head_dim 128, 2 bytes/element) a single 32K-token sequence costs ~10.7 GB on
top of weights. Whole-proof provers emit 8K–32K token proofs, so KV is not free at the
large end and is one more reason 32B class with 4-bit weights is the practical ceiling
on a single 80 GB card.

**Quantisation availability.** Third-party GGUF builds of Goedel-Prover-V2-32B exist,
e.g. Q4_K_S at 18.9 GB and Q4_K_M at 19.9 GB ([mradermacher](https://huggingface.co/mradermacher/Goedel-Prover-V2-32B-GGUF)),
and a mirrored 18.8 GB Q4_K_S ([DevQuasar](https://huggingface.co/DevQuasar/Goedel-LM.Goedel-Prover-V2-32B-GGUF)).
`UNVERIFIED:` I found no published measurement of how 4-bit quantisation affects **Lean
proof validity** for any prover. Quantisation degrades closed-vocabulary syntax
reliability, and a prover's output is all closed-vocabulary syntax, so I would expect a
disproportionate hit — but that is my inference, not a cited result. Measure it on
miniF2F yourself before trusting a quantised prover.

---

## 2. Agentic and general-reasoning systems

The dividing line in 2026 is no longer "specialised prover vs. general model". It is
"can the system run a long generate-verify-repair loop against a real Lean toolchain".

### 2.1 Aristotle (Harmonic) — the one you can actually call

Aristotle combines a Lean proof-search algorithm (highly parallel Monte Carlo Graph
Search with a transformer policy/value), a lemma-based informal reasoning system that
generates and formalises lemmas, and a geometry solver ([paper](https://arxiv.org/pdf/2510.01346)).
It is exposed as an **asynchronous HTTP API** — submit a job, poll, download the result —
driven by the `aristotlelib` Python SDK or the `aristotle` CLI
([API docs](https://apis.io/apis/harmonic/aristotle-api/),
[PyPI](https://pypi.org/project/aristotlelib/)). Supported modes: fill `sorry`s inside an
existing Lean project (`aristotle submit "Fill in all sorries" --project-dir ./my-lean-project`),
formalise a LaTeX/markdown document (`aristotle formalize paper.tex`), or prove from a
plain-language problem file ([PyPI](https://pypi.org/project/aristotlelib/)).

Two documented caveats, both load-bearing:

- **Partial success is normal and is reported honestly.** A published case study of an
  Aristotle API attempt on the Grasshopper problem (IMO 2009 P6) reports four verified
  helper lemmas and a main theorem "closed directly by one unresolved `sorry`" — local
  proof search succeeded, the global counting argument did not
  ([paper](https://arxiv.org/html/2605.20120v1)). You must read the output for `sorry`,
  not the success banner.
- **Aristotle is a component, not a solution.** The complete machine-checked
  formalisation of Alpöge's unit-distance disproof was produced by an orchestrated
  ensemble — Claude (Anthropic), Aristotle (Harmonic), and Codex (OpenAI) — directed from
  a single Claude Code session, over one working day
  ([kim-em/erdos-unit-distance](https://github.com/kim-em/erdos-unit-distance)).

Boris Alexeev used Aristotle with a repository formalisation to prove Erdős Problem 124
([Formal Conjectures paper](https://arxiv.org/html/2605.13171v1)).

### 2.2 AlphaProof / AlphaProof Nexus (DeepMind)

The headline number for this appendix: the most capable AlphaProof Nexus agent
**autonomously resolved 9 of 353 open Erdős problems at a per-problem inference cost of a
few hundred dollars**, proved 44/492 OEIS conjectures, and was deployed in combinatorics,
optimization, graph theory, algebraic geometry and quantum optics research
([paper](https://arxiv.org/html/2605.22763v1)). The 353 problems were every Lean statement
of an Erdős problem available in Formal Conjectures as of early February 2026, capped at
3000 episodes each, with expert validation that the Lean statement faithfully captured the
original conjecture ([paper](https://arxiv.org/html/2605.22763v1)). Proofs are released at
[google-deepmind/alphaproof-nexus-results](https://github.com/google-deepmind/alphaproof-nexus-results).

The design finding matters more than the score: a **basic agent alternating LLM generation
with Lean verification replicated the Erdős successes**, while AlphaProof itself, run
standalone in tree-search inference mode with ~64 v6e TPU hours per problem, **solved none
of the nine** ([paper](https://arxiv.org/html/2605.22763v1),
[analysis](https://www.howardism.dev/articles/alphaproof-nexus)). Agentic loop beats bespoke
prover at this frontier; the LLM does the mathematics and Lean is the filter.

### 2.3 Aletheia (DeepMind, Gemini Deep Think)

A generate-verify-revise agent that iterates entirely in natural language with an
inference-time scaling law and tool use ([paper](https://arxiv.org/pdf/2602.10177v1)).
Evaluated on 700 conjectures labelled "Open" in Bloom's Erdős database, it autonomously
solved **four** — Erdős-652, -654, -1040, -1051 ([report](https://arxiv.org/pdf/2601.22401v2),
[summary](https://medium.com/@reliabledataengineering/aletheia-google-deepminds-ai-just-solved-4-erd%C5%91s-problems-autonomously-9f2b846e0c47)).
Note the ratio: 4/700. That is the honest base rate for "point a frontier agent at an
arbitrary open problem".

### 2.4 OpenAI

**Unit distance (May 2026).** An internal OpenAI general-purpose reasoning model disproved
Erdős's 1946 planar unit-distance conjecture, constructing configurations with at least
n^(1+δ) unit-distance pairs for fixed δ>0; Will Sawin's refinement gives δ=0.014
([announcement](https://openai.com/index/model-disproves-discrete-geometry-conjecture/)).
Nine external mathematicians contributed a companion paper with a streamlined human
version ([Quanta](https://www.quantamagazine.org/why-the-legendary-erdos-problems-are-falling-to-ai-20260803/)).
The model was explicitly **not** a maths-specific system, not scaffolded for proof search,
and not targeted at this problem ([announcement](https://openai.com/index/model-disproves-discrete-geometry-conjecture/)).
This is the strongest single data point that **counterexample search on a famous open
problem is a general-reasoning task, not a prover task**.

Downstream: within weeks of the OpenAI announcement, Bloom, Sawin, Schildkraut and
Zhelezov disproved the Erdős–Szemerédi sum-product conjecture over the reals
([Kalai](https://gilkalai.wordpress.com/2026/05/21/amazing-erdos-unit-distance-problem-was-disproved-it-was-achieved-by-ai/)),
and a group used OpenAI's internal model to settle a problem about electrical flow in
graphs ([Kalai](https://gilkalai.wordpress.com/2026/05/21/amazing-erdos-unit-distance-problem-was-disproved-it-was-achieved-by-ai/)).

**GPT-5.6 Sol.** Reported results include a proof of the cycle double cover conjecture
from 64 concurrent subagents ([registry entry](https://whataifound.org/finding/2026-07-10-cycle-double-cover)),
a near-quadratic lower bound closing a 30-year oracle-complexity gap in derivative-free
convex optimisation, Lean-verified ([preprint](https://arxiv.org/pdf/2607.13335),
[account](https://stackfutures.com/blog/gpt-56-sol-convex-optimization-30-year-lean-verified)),
and a Lean formalisation of the unit-distance proof generating 1.2M lines of Lean over
three weeks ([account](https://stackfutures.com/blog/gpt-sol-erdos-lean-formalization)).
`UNVERIFIED:` the 1.2M-line figure and the "Buzzard confirmed it in a sandbox" detail come
from a secondary blog summary; I did not find a primary OpenAI or Buzzard post. Treat it
as reported, not established.

### 2.5 Anthropic / Claude

**The Jacobian conjecture counterexample (July 2026).** Levent Alpöge announced on
20 July 2026 an explicit polynomial map F : ℂ³ → ℂ³ with det Jac F ≡ −2 that sends three
distinct points to a common image, crediting the question to Akhil Mathew and the
construction to **Claude Fable 5** ([MathWorld](https://mathworld.wolfram.com/JacobianConjecture.html),
[John D. Cook](https://www.johndcook.com/blog/2026/07/21/jacobian-conjecture)). The map is short enough to fit in a single post
([SciDaily summary](https://www.sciencedaily.com/releases/2026/08/260804034634.htm)).

Verification status, carefully: the counterexample is checkable by exact rational
arithmetic, and an **independent Lean 4 formalisation** of the Alpöge–Fable map exists,
explicitly *not* claiming originality, whose sole original content is the Lean
formalisation and build log ([Zenodo record](https://zenodo.org/records/21514514)).
Shuhong Gao generalised the construction to every dimension n > 2 with arbitrarily large
geometric degree, verified in exact rational arithmetic with Gröbner-basis fibre analysis
([arXiv:2608.00222](https://arxiv.org/abs/2608.00222)). Gallagher gave an infinite family
the next day and Speyer a geometric explanation two days later
([arXiv:2608.00222](https://arxiv.org/abs/2608.00222)). This is as close to settled as an
announced counterexample gets.

**Fermat's Last Theorem.** Claude produced the first end-to-end computer-checked proof of
FLT, working largely autonomously over 11 days, 29,511 theorems and ~13M lines of Lean
(~10.5M without generated boilerplate) ([Anthropic](https://www.anthropic.com/research/formalizing-fermats-last-theorem),
[technical note](https://www-cdn.anthropic.com/9e431dff043da6538d99d6c2d231b670aa3da263.pdf)).
The checking story is the useful part: Prove2Me marks a card "Proved" after compiling it
against only its children's statements, which is **not** an end-to-end check; the team
then recompiled all 29,511 cards from source outside the platform, built the whole tree as
a single Lean project, and ran `leanprover/comparator` and `nanoda` (an independent Rust
reimplementation of Lean's kernel) on the release
([technical note](https://www-cdn.anthropic.com/9e431dff043da6538d99d6c2d231b670aa3da263.pdf)).
Anthropic's own note quotes the agent saying the honest sentence was "proved on prove2me,
pending the independent re-check" rather than "FLT is formalized"
([technical note](https://www-cdn.anthropic.com/9e431dff043da6538d99d6c2d231b670aa3da263.pdf)).
Read that as the template for how you should describe your own results.

### 2.6 The Dinitz–Garg–Goemans counterexample (July 2026)

Dmitry Rybin used **GPT-5.6 Pro** with four short prompts to construct a counterexample to
the cost-preserving unsplittable-flow conjecture open since the late 1990s: a directed
graph on seven nodes with three demands (15, 10, 15) whose fractional solution costs 58
while every unsplittable routing within the allowed capacity cushion costs at least 60
([registry entry](https://whataifound.org/finding/2026-07-22-dinitz-garg-goemans)).
The model returned proof certificates, an exhaustive-enumeration verification program,
machine-readable data and LaTeX source; it initially returned nothing, and produced the
result after several hours and three "keep going" prompts
([account](https://news.bpdata.com/article/ai-finds-counterexample-to-30-year-old-graph-theory-739c05c9),
[account](https://officechai.com/ai/mathematician-says-gpt-5-6-disproved-the-30-year-old-dinitz-garg-goemans-conjecture-with-4-simple-prompts)).
**Status caveat:** the registry grades this entry verification = *Claimed*, autonomy =
*AI-led*, and notes it has not been peer reviewed
([registry](https://whataifound.org/finding/2026-07-22-dinitz-garg-goemans)); several people
checked the arithmetic and found it consistent
([account](https://datacamp.com/blog/gpt-5-6-dinitz-garg-goemans-conjecture)). It is a
concrete finite graph checkable by direct computation. `UNVERIFIED:` I found no Lean
formalisation of this counterexample.

### 2.7 Parallel-agent results worth knowing about

Star Fleet Math is a Mac app driving up to 20 agentic "starships", each a GPT-5.6
instance on a dedicated 60-vCPU server, one problem each
([site](https://www.starfleetmath.com/)). Its own front page reports **19 Erdős problems**
solved ([site](https://www.starfleetmath.com/)); secondary coverage rounds this to 20
([summary](https://o16g.com/resources/)). Its downloads include the pinned Lean project
and a verifier script so you can check independently
([site](https://www.starfleetmath.com/)) — do that if you cite it.

---

## 3. Tooling and harnesses

### 3.1 The verification harness you will actually be held to

`leanprover/comparator` (Apache-2.0) is the tool the subnet pins
([repo](https://github.com/leanprover/comparator)). It takes a `Challenge.lean` containing
the theorem with a `sorry`, a `Solution.lean` from you, a JSON config listing
`permitted_axioms`, and asserts three things: your solution proves the same statement, uses
no more axioms than permitted, and is accepted by the Lean kernel
([repo](https://github.com/leanprover/comparator)). It depends on `landrun` for sandboxing
and `lean4export`, and can be configured with additional external kernels via
`external_kernels` ([repo](https://github.com/leanprover/comparator)). The subnet's config
uses exactly `["propext", "Quot.sound", "Classical.choice"]`, matching the conventional
Lean-4-mathematics trusted base ([comparator README](https://github.com/leanprover/comparator),
conjectures.io status page above). Comparator was developed by Lean FRO with the AIMO team
"to enable trustworthy LLM Lean evaluation on Kaggle"
([repo](https://github.com/leanprover/comparator)).

### 3.2 Subnet-66-specific tooling

| Repo | What it is |
|---|---|
| [conjectures-miner](https://github.com/conjectures-io/conjectures-miner) | Miner CLI. `install.sh`; `conjectures config set api_base_url`; `tasks sync` caches the allowlist offline; `tasks list --filter erdos`; `tasks challenge <task>` writes `challenges/<task_id>/Challenge.lean` and prints `task_mode` (a `counterexample` task wants the negation); `build --proof Main.lean --task <id>` writes `submission.zip` + `submission.plan.json`; `check` is the free static policy check; `pay` fills the payment slot. Your `Main.lean` holds declarations only — it is inserted between a trusted header and footer supplying imports and the namespace. |
| [conjectures-validator](https://github.com/conjectures-io/conjectures-validator) | The full validator: paid submission API (0.5 TAO/attempt), payment confirmation on finalized chain state, per-proof networkless Lean container, immutable verifier reports, reward eligibility, treasury-only weight submission. |
| [conjectures-tasks](https://github.com/conjectures-io/conjectures-tasks) | Versioned immutable task bundles. 418 bundles / 209 audited direct propositions (189 Erdős + 20 Green). Each bundle: challenge, manifest, comparator config, trusted hashes, solution wrapper. Content-addressed; a changed challenge requires a new task id. `POOL.md` holds the deny-by-default allowlist and selection audits. |
| [conjectures-contribution](https://github.com/conjectures-io/conjectures-contribution) | Partial work — a lemma, definition, API, special case, tactic — submitted as pull requests. Explicitly *not* for full solutions, which go to the validator. Defines recognition weights and funded paid events. |
| [conjectures-io/formal-conjectures](https://github.com/conjectures-io) | The subnet's mirror/pin of DeepMind's Formal Conjectures. |

**The practical trap in the miner CLI.** `Main.lean` is inserted under a trusted
header/footer, so an `import` line of your own is a refusal, not a duplicate. Also refused:
`sorry`, `admit`, `axiom`, `set_option`, `native_decide`, `instance`, attributes,
`macro`/`syntax`/`notation`, and any reference to the source theorem
([miner README](https://github.com/conjectures-io/conjectures-miner)). Now look at the
canonical inference prompt for every dedicated prover — Goedel-Prover-V2's own model card
prompt is `import Mathlib` / `import Aesop` / `set_option maxHeartbeats 0` /
`open BigOperators Real Nat Topology Rat` followed by the theorem with `sorry`
([card](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-32B)); Kimina's is the same shape
([card](https://huggingface.co/AI-MO/Kimina-Prover-72B)). **Raw prover output will be
rejected by the static check.** You must strip the prelude, delete `set_option`, and
rewrite any `native_decide` closing into a proof term that does not pull in
`Lean.ofReduceBool`. That last point is not hypothetical — see §4.

### 3.3 Search, retrieval, and agent harnesses

| Tool | What it gives you | Link |
|---|---|---|
| **Aesop** | White-box best-first proof search tactic for Lean 4; distinguished paper, CPP 2023. Systematic rule application with recursive subgoal search. | [repo](https://github.com/leanprover-community/aesop), [paper](https://people.compute.dtu.dk/ahfrom/aesop-camera-ready.pdf) |
| **leansearch** | Natural-language Mathlib search; also exposed as `#leansearch` command/term/tactic via LeanSearchClient. | [LeanSearchClient docs](https://eshelyaron.com/man/lean4-bdd/LeanSearchClient/LoogleSyntax.html) |
| **LeanSearch v2** | Two-mode retrieval: standard mode (hierarchy-informalized Mathlib corpus + embedding–reranker) at nDCG@10 = 0.62 vs 0.53 for the next-best system; reasoning mode does iterative sketch-retrieve-reflect for *global* premise retrieval. API at leansearch.net. | [paper](https://arxiv.org/pdf/2605.13137.pdf) |
| **Loogle** | Type-pattern search over Mathlib (`?a → ?b → _`), constant / name-substring / subexpression filters; `#loogle` syntax; `--loogle-local` builds a ~6 GB index. | [docs](https://eshelyaron.com/man/lean4-bdd/LeanSearchClient/LoogleSyntax.html), [slides](https://leaning.in/2026/slides/dressler.pdf) |
| **Moogle** | `#moogle` search, same three syntactic forms. | [docs](https://eshelyaron.com/man/lean4-bdd/LeanSearchClient/LoogleSyntax.html) |
| **ReProver** | LeanDojo's retrieval-augmented prover: ByT5 encoder–decoder mapping goals to tactics, DPR premise retrieval, beam search at inference; the model behind Lean Copilot's premise selection. | [review](https://themoonlight.io/en/review/lean-copilot-large-language-models-as-copilots-for-theorem-proving-in-lean) |
| **Lean Copilot** | Neuro-symbolic framework embedding LLM inference *inside* Lean via native C++ FFI: `suggest_tactics`, `search_proofs` (drop-in aesop replacement that can call goal-dependent generated tactics at each node), `select_premises` (BLAS matrix–vector over a precomputed premise embedding matrix). | [paper](https://arxiv.org/html/2404.12534) |
| **LeanExplore** | Search engine over Lean 4 declarations, with an MCP server exposing it as tools. | [paper](https://arxiv.org/html/2506.11085v1) |
| **lean-lsp-mcp** | The de-facto agent harness: MCP server over Lean's LSP plus external search services. Tools include `lean_goal`, `lean_multi_attempt`, `lean_diagnostic_messages`, `lean_run_code`, `lean_verify`, `lean_local_search`, `lean_leansearch`, `lean_loogle`, `lean_leanfinder`, `lean_state_search`, `lean_hammer_premise`, `lean_code_actions`, `lean_profile_proof`. | [repo](https://github.com/oOo0oOo/lean-lsp-mcp), [slides](https://leaning.in/2026/slides/dressler.pdf) |
| **lean-tools-mcp** | Alternative MCP server with a larger tool set including `lean_unified_search`, `lean_analyze_deps`, `lean_export_decls`. Its README also points at `lean-docker-mcp` and LeanTool as other Lean MCP projects. | [repo](https://github.com/optsuite/lean-tools-mcp) |
| **lean4-skills** | A Claude Code / Cline / Windsurf skill pack with a cycle engine: LSP-first inspection, time-boxed search budgets (~30 s), explicit "stuck" definitions, `simp only [...]` / `grind [...]` candidate generation from `lean_hammer_premise`. | [repo](https://github.com/cameronfreer/lean4-skills) |
| **Snapshotting for tactic search** | Making parallel tactic search over partially specified proofs cheap. | [paper](https://arxiv.org/html/2605.25556v2) |

**What is worth your time from that table.** The `lean-lsp-mcp` usage statistics from a
real large-scale run are the most useful empirical guide I found
([slides](https://leaning.in/2026/slides/dressler.pdf)):

| Tool | Calls | Success | Avg time |
|---|---|---|---|
| `lean_local_search` | 2658 | 99.5% | 0.3 s |
| `lean_run_code` | 2356 | 98.9% | 7.3 s |
| `lean_loogle` | 1411 | 42.6% | 1.0 s |
| `lean_leansearch` | 955 | 89.8% | 0.7 s |
| `lean_leanfinder` | 153 | 100% | 1.1 s |
| `lean_goal` | 100 | 88.0% | 10.0 s |
| `lean_diagnostic_messages` | 88 | 23.9% | 48.2 s |
| `lean_hammer_premise` | 19 | 73.7% | 0.6 s |

`lean_local_search` (ripgrep over your project + Mathlib) is both the most-used and the
most reliable; `lean_diagnostic_messages` is slow and usually fails, so do not build a
loop that depends on it. In the same case study, 272,132 lines of Lean were written at a
cost of 210M model tokens, with Lean wall-time of ~26.3 hours
([slides](https://leaning.in/2026/slides/dressler.pdf)). That is your realistic
throughput figure.

### 3.4 Datasets

| Dataset | Size | Link |
|---|---|---|
| LeanWorkbook | 57,231 problems; LeanWorkbook Plus 82,893; ~5k with formal solutions; manual sample accuracy 93.5% | [paper](https://arxiv.org/html/2406.03847v2), [HF](https://huggingface.co/datasets/InternLM/Lean-Workbook) |
| Goedel-Prover / Lean-workbook-proofs | 29.7K Lean Workbench proofs, ~2× the prior 15.7K | [HF](https://huggingface.co/datasets/Goedel-LM/Lean-workbook-proofs) |
| Numina / Kimina | Project Numina co-released the Kimina family and an autoformalizer; NuminaMath-LEAN is a substrate for OProofs | [Kimina repo](https://github.com/MoonshotAI/Kimina-Prover-Preview) |
| OProofs | ~1.77M Lean statements, 6.86M compiler-verified proofs, with retrieved context, failed attempts and repair trajectories | [paper](https://arxiv.org/abs/2605.17283) |
| Goedel-Prover-V2 SFT / RL sets | 1,745,010 SFT samples; RL set with `lean4_completion` and `lean4_revision` subsets | [SFT](https://huggingface.co/datasets/Goedel-LM/SFT_dataset_v2), [RL](https://huggingface.co/datasets/Goedel-LM/RL_dataset_V2) |
| miniF2F-ALF | ALF-mutated contamination-sensitive perturbation benchmark; every evaluated model loses accuracy on it | [paper](https://arxiv.org/pdf/2606.12594) |

---

## 4. Critical: what the benchmarks do and do not establish

### 4.1 ProofGate

The ICML 2026 paper *"ProofGate: A Reproducible Audit of Faithfulness, Alignment, and
Vacuity in State-of-the-Art Lean Theorem Provers"* defines four orthogonal checks —
kernel-level axiom inspection, a banned-tactic linter, a negation-counterexample probe for
vacuity, and a FormalAlign-style alignment score — combined into one dimensionless metric,
**Faithful-Pass**. A single failed check disqualifies an item. It applies them to every
publicly released proof artifact of three SOTA systems
([ICML page](https://icml.cc/virtual/2026/82433)).

**Finding 1 — DeepSeek and Kimina hold up.** Kernel-level audit of all 635 DeepSeek-Prover-V2
(miniF2F-test and -valid combined) and Kimina-Prover-72B miniF2F-test proofs against each
prover's pinned Mathlib revision gives Kernel-Faithful-Pass = 100%, with no `sorry` and no
extra axioms beyond the compiler-trust set. Under the **strict** trusted base, all 438
DeepSeek proofs pass while 186/197 Kimina proofs pass — **the eleven exceptions are
precisely those that invoke `native_decide`** ([ICML page](https://icml.cc/virtual/2026/82433)).

This is the single most actionable finding in this appendix for a conjectures.io miner.
`native_decide` is explicitly on the subnet's refusal list
([miner README](https://github.com/conjectures-io/conjectures-miner)), and ProofGate shows
it is the *only* thing that broke an otherwise clean set of 197 real proofs. If your
pipeline ever emits a `native_decide` closing, it is dead on arrival — and it appears in
prover output often enough to be 5.6% of Kimina's released miniF2F solutions.

**Finding 2 — alignment is a real leak.** SBERT-based alignment scoring returns a **15.2%
misalignment rate on DeepSeek miniF2F-test**, within 1.2 percentage points of ReForm's
expert-annotated rate ([ICML page](https://icml.cc/virtual/2026/82433)). In other words
roughly one in seven "proved problems" is a proof of a statement that does not faithfully
represent the informal problem. This is the mechanism by which a benchmark score inflates
without anyone lying.

**Finding 3 — the Goedel-Prover-V2 claim.** The abstract states: "Goedel-Prover-V2's
'released proofs' for miniF2F are in fact the benchmark input statements with `sorry`
placeholders; the public release contains no auditable proofs, a property the accompanying
paper does not state explicitly" ([ICML page](https://icml.cc/virtual/2026/82433)).

**How well can I verify this?** Partially, and you should know exactly which part.

- **Restatement confirmed.** The claim appears verbatim in the ICML 2026 abstract page
  ([link](https://icml.cc/virtual/2026/82433)) and in the artifact repository README
  ([github.com/edisonly1/proofgate](https://github.com/edisonly1/proofgate)). `UNVERIFIED:`
  the OpenReview PDF (`openreview.net/pdf?id=uMTF54muYL`) is behind a Cloudflare browser
  challenge that I could not clear, so I read the abstract and the repo, not the full
  paper's methodology section.
- **These are not two independent sources.** The GitHub repo is the *same group's* artifact
  release (MIT, created 2026-06-20, 2 commits), not a third party reproducing the finding
  ([repo](https://github.com/edisonly1/proofgate)). I found no independent replication.
  Treat Finding 3 as one team's audit, well-specified and reproducible in principle, not as
  consensus.
- **The structural claim I could corroborate myself.** Goedel-Prover-V2's public release
  consists of model weights plus *training* datasets (`SFT_dataset_v2`, `RL_dataset_V2`,
  [HF](https://huggingface.co/datasets/Goedel-LM/SFT_dataset_v2),
  [HF](https://huggingface.co/datasets/Goedel-LM/RL_dataset_V2)) and its README points at
  the model card and arXiv paper, not at a benchmark proof archive
  ([repo](https://github.com/Goedel-LM/Goedel-Prover-V2)). By contrast, DeepSeek-Prover-V2's
  README explicitly says "The proofs generated by DeepSeek-Prover-V2 for the miniF2F
  dataset are available for download as a ZIP archive"
  ([README](https://github.com/deepseek-ai/DeepSeek-Prover-V2/blob/main/README.md)), and
  Kimina's repo says "All proofs found by Kimina-Prover Preview in miniF2F-test are also
  released in this repo (zipped to avoid contamination)"
  ([repo](https://github.com/MoonshotAI/Kimina-Prover-Preview)). Goedel-Prover V1 *does*
  release proofs, but for Lean Workbook (29.7K), not miniF2F
  ([repo](https://github.com/Goedel-LM/Goedel-Prover)). So the asymmetry ProofGate describes
  — auditable artifacts for two systems, none for the third — is visible in the public
  release surface, which is independent corroboration of the *shape* of the claim even
  though it cannot confirm the `sorry`-placeholder detail.
- **A related claim I could not verify.** A search-result fragment of the ProofGate PDF
  reads in part "…contains training data from Goedel-Prover-V1, and MathOlympiadBench
  contains benchmark statements with sorry placeholders." I could not load the PDF to read
  this in context, so what it asserts about MathOlympiadBench is `UNVERIFIED:`.

**What this implies for you.** Do not cite a benchmark number whose proof artifacts you
cannot inspect yourself. When a number appears on a model card without an archived
per-problem proof set, treat it as a claim. When you submit to conjectures.io this is
moot — the kernel decides — but your *stack selection* is being made on exactly these
numbers.

### 4.2 Benchmark-auditing caveats that are independent of ProofGate

**miniF2F has known bad problems, and the fixes moved.** Kimina's teams identified and
corrected **eight unsolvable problems** in the benchmark
(`mathd_numbertheory_618`, `aime_1994_p3`, `amc12a_2021_p9`, `mathd_algebra_342`,
`mathd_numbertheory_343`, `mathd_algebra_158`, `induction_pord1p1on2powklt5on2`,
`induction_prod1p1onk3le3m1onn`), releasing corrected versions via the Numina HuggingFace
repository ([paper](https://arxiv.org/html/2504.11354v1)). The same repo note says Kimina
"helped to identify at least 5 problems in the miniF2F-test dataset that were wrongly
formalized" ([repo](https://github.com/MoonshotAI/Kimina-Prover-Preview)). A benchmark
whose ground truth is being repaired after the fact cannot be a stable yardstick.

**miniF2F's problem statements are themselves autoformalization of a syntactically
simplified problem.** A NeurIPS 2025 Datasets & Benchmarks paper, *miniF2F-Lean Revisited*,
evaluates full autoformalize→prove pipelines and reports that the best accuracy on their
rebuilt `miniF2F-v2` is 70% vs 40% on original miniF2F, with translation failures
(statements that compile but do not match the informal problem) as a distinct failure mode,
and shows the LLM judge produces false positives and reports much higher accuracy than a
human evaluator ([paper](https://proceedings.neurips.cc/paper_files/paper/2025/file/72dad95a24fae750f8ab1cb3dab5e58d-Paper-Conference.pdf)).

**Real-world proofs are a different benchmark.** SorryDB asks whether AI provers can
complete real-world Lean theorems — i.e. goals arising in actual projects rather than
competition statements ([paper](https://arxiv.org/html/2603.02668v2)). miniF2F competence
does not transfer to Mathlib-shaped goals, which is what you face here.

### 4.3 Contamination, and why the Erdős pool is a special case

**The formal-conjectures authors frame open problems as a zero-contamination testbed.**
The benchmark is 2,615 Lean-4 statements, of which **1,029 are open research conjectures
described as a zero-contamination benchmark for proof discovery**, with 836 solved problems
used for autoformalization ([paper](https://arxiv.org/abs/2605.13171)). The Erdős source
collection within it is 1,318 problems, **551 research-open**, 551 research-solved, 216
other ([paper](https://arxiv.org/html/2605.13171v1)).

**But the same paper states the limitation plainly:** "for solved problems, models may
retrieve known arguments rather than reasoning from scratch; for open problems,
zero-contamination is not permanent as future solutions enter training data"
([paper](https://arxiv.org/html/2605.13171v1)).

**The strongest available anti-contamination argument, and its exact limits.** Epoch AI's
FrontierMath Erdős benchmark — 68 conjectures covering 65 problems, **50 of the 68
statements taken from Formal Conjectures** with the remaining 17 autoformalized and
individually reviewed by Thomas Bloom — states: "No proof of any of the 68 conjectures was
known as of August 2026, so a model whose training cutoff predates that date cannot have
learned one" ([Epoch AI](https://epoch.ai/benchmarks/frontiermath-erdos)). That is a
correct argument about *proofs*. It is not an argument about *commentary*: Erdős problems
are famous, published and heavily discussed, so any model trained after 2024 has very
likely seen the problem statements, partial results, failed attacks, and discussion of what
the answer is expected to be. Contamination of the *answer* is unlikely; contamination of
the *prior*, the search heuristics, and the "which approaches have been tried" distribution
is near-certain. For a prover that is the difference between reasoning and recall; for a
search-based counterexample hunt it is less of a problem, because a construction still has
to check out in the kernel.

**The failure mode that actually bites: the target may not be open.** The Gemini Erős case
study stresses that "'Open' status of a problem in this database does not always reflect the
true state of the literature," quoting the editors — "in practice, a problem being listed
as 'open' roughly indicates that at least 1 professional mathematician attempted and failed
to find a previously published solution by searching the internet" — and notes that in
October 2025 OpenAI announced GPT-5 had identified **ten "Open" problems on the site that
had already been resolved in the literature**
([paper](https://arxiv.org/pdf/2601.22401v2)). So before you spend compute, search the
literature yourself. A rediscovered proof is a rejection, and on this subnet submissions
"lifted from an unmerged pull request or a public source" are disqualifying
([FAQ](https://conjectures.io/faq)).

### 4.4 The vacuities are showing up in production, on this subnet

This is the most important section for a conjectures.io miner, because it is empirical data
from the actual pool rather than from miniF2F.

**Documented case — Erdős problem 726.** The published Lean source used
`(n % p : ℝ)`, which elaborates as *real-field* modulo `(n : ℝ) % (p : ℝ)` rather than
casting the natural-number residue. For every prime `p` this reduces to
`n - p * (n / p) = 0`, making the filter condition `p/2 < 0` impossible and the sum
identically zero. The submitted proof **validly refuted that degenerate frozen statement**
by contrasting the zero function with `(log (log n))/2` — but it does not refute the
intended integer-residue asymptotic. The team awarded a **$750 USD-equivalent
formalization-defect award** instead of the displayed 935.1993 Alpha bounty, and quarantined
the task ([results page](https://conjectures.io/results/bd1a524a-c56e-42f2-9075-443df43468d7)).
Read that sentence again: the Lean kernel accepted a counterexample, the static policy
check passed, fourteen gates passed, and the mathematics was still wrong. The published
statement was broken, not the miner's proof.

**This is a pattern, not an incident.** The review decision for Green's Open Problem 29
notes that "the three preceding approvals of a `FORMALIZATION_DEFECT_AWARD` — Erdős 15,
Green 42, Erdős 939 — each turned on a defective definition in the published source"
([review decision](https://github.com/conjectures-io/conjectures-validator/blob/main/docs/review-decisions/2026-08-06-green-29.md)).
Against a results page reading "Showing 9 of 13," that means a substantial fraction of the
earliest accepted submissions were defect awards. Green 29 itself is described as the first
submission under policy v1 that "neither exploits a formalization defect nor duplicates an
earlier claim," and its review doc is worth reading in full as a model of what a rigorous
pre-submission self-check looks like: the reviewer traces each lemma against the pinned
Mathlib, checks that the covering argument was verified element by element for coordinates
−2…2, confirms that `S⁸ ⊆ A⁴` is used in the strong direction rather than weakened,
confirms that `ULift` is universe bookkeeping doing no mathematical work, and confirms the
target is bound through `fcTypeOfName%` so no statement substitution is possible
([review decision](https://github.com/conjectures-io/conjectures-validator/blob/main/docs/review-decisions/2026-08-06-green-29.md)).

**Operational consequences for you.**

1. **Read `Challenge.lean` before optimizing anything.** The failure mode of the pool so
   far is a defective frozen statement, not a bad prover. If the Lean statement is
   degenerate — a vacuous filter, a coercion that collapses the type, a hypothesis that
   makes the conclusion trivial — a counterexample is *easy* and pays a defect award rather
   than the bounty. If that is your goal, say so; if it is not, spend twenty minutes on the
   statement before you spend GPU-hours on the mathematics.
2. **Prefer the strongest kernel check available.** The subnet's own policy forbids
   `native_decide`, which is exactly the construct that broke 11/197 otherwise-clean Kimina
   proofs under ProofGate's strict trusted base. Run a `#print axioms` audit on every proof
   you generate before you pay 0.5 TAO.
3. **The site is candid that its own framework may be wrong.** "That review is the reason a
   Lean statement can be trusted to mean what the original conjecture meant — and it is the
   one place where the whole design could still be wrong, which is why we would rather hear
   about a bad formalization early" ([how-it-works](https://conjectures.io/how-it-works)).
   Take them at their word.

---

## 5. Practical recommendation

### 5.1 The two attack modes are different problems with different stacks

| | (a) Prove the statement | (b) Find a counterexample |
|---|---|---|
| What you must produce | a closed Lean proof term for the published theorem | a Lean proof of the **negation** — i.e. an explicit construction, formalised |
| Where the difficulty lives | bridging a known-but-hard proof into Lean's elaboration | discovering a construction nobody has found |
| Best tool class | dedicated prover + agentic lemma decomposition | strong general reasoning model + search, then a Lean formalisation step |
| Evidence | Goedel-Prover-V2, Kimina, Oprover, Seed-Prover all target exactly this | the Jacobian, Dinitz–Garg–Goemans, and unit-distance results were **all** found by general models, and the Jacobian and unit-distance ones were formalised **after** discovery |
| Failure mode you should expect | running out of context/compute with a near-proof | a construction that does not close in Lean, or one that refutes a degenerate statement |

The asymmetry is the most decision-relevant fact in this document. Every 2026 breakthrough
counterexample I could find was found by a general reasoning model:

- **Jacobian conjecture, dimension 3** — Claude Fable 5, found July 2026, credited to a
  general model used as a research collaborator, by a working mathematician
  ([MathWorld](https://mathworld.wolfram.com/JacobianConjecture.html),
  [SciDaily](https://www.sciencedaily.com/releases/2026/08/260804034634.htm)).
- **Dinitz–Garg–Goemans** — GPT-5.6 Pro, four prompts, hours of unattended compute
  ([registry](https://whataifound.org/finding/2026-07-22-dinitz-garg-goemans)).
- **Erdős unit distance** — an internal general-purpose OpenAI model, explicitly not a
  maths system ([announcement](https://openai.com/index/model-disproves-discrete-geometry-conjecture/)).

And on the proof side, the DeepMind result is the same story in a different register: the
*basic* agent using a frontier LLM in a generate-verify loop replicated the Erdős successes
that a bespoke RL prover could not achieve standalone
([paper](https://arxiv.org/html/2605.22763v1)).

**So: do not buy GPUs to run a prover. Buy a prover to run a search, or rent an API.**

### 5.2 Concrete stacks, in the order I would build them

**Phase 0 — the harness and the free check. Do this before anything else.**
Install `conjectures-miner`, point it at a validator, `conjectures tasks sync`, pick a task,
`conjectures tasks challenge <task>` ([miner README](https://github.com/conjectures-io/conjectures-miner)).
Build a local Lean environment at the pinned toolchain — Lean `v4.27.0`, Mathlib
`a3a10db0e9d6`, Comparator `68a064109f01` ([status](https://conjectures.io/status)) — and
run `conjectures check` in a loop. This is free, unauthenticated, opens no key, and runs the
same admission and static policy check the validator runs
([submit-a-proof](https://conjectures.io/submit-a-proof)). Cost per actual attempt is
0.5 TAO ([how-it-works](https://conjectures.io/how-it-works)).

Write the *prelude stripper* here, not later. Your prover will emit `import Mathlib`,
`set_option maxHeartbeats 0` and `open BigOperators Real Nat Topology Rat`
([card](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-32B)); your harness must strip
them before `conjectures check` sees the file. Also write the `native_decide` rewriter.
And build a `#print axioms` assertion into your own pipeline so you never pay for a proof
whose trusted base is larger than `propext`, `Quot.sound`, `Classical.choice`.

**Phase 1 — API-only, no GPUs. This is where I would spend the first two weeks.**
Frontier model + `lean-lsp-mcp` + pinned Mathlib + the loop the DeepMind basic agent used
([paper](https://arxiv.org/html/2605.22763v1), [repo](https://github.com/oOo0oOo/lean-lsp-mcp)).
Budget against the only published per-problem figure for this activity: **a few hundred
dollars per problem** at a 9/353 success rate
([paper](https://arxiv.org/html/2605.22763v1)). Note the base rate before you spend: 9/353
for the best agent, and 4/700 for Aletheia on a broader open-problem database
([paper](https://arxiv.org/pdf/2601.22401v2)). At $300/problem, sweeping all 209 targets
is ~$63k for an expected ~5 solves; sweeping 20 hand-picked ones is ~$6k. Pick the 20.

Design the loop from the DeepMind findings, which are specific: have the agent decompose to
lemmas, prove each, and let a *simple* loop do the work — the "basic" design matched the
full-featured one on all nine Erdős solves, while the bespoke prover contributed nothing
standalone ([paper](https://arxiv.org/html/2605.22763v1),
[analysis](https://www.howardism.dev/articles/alphaproof-nexus)). Use Aristotle's API in the
same loop for the hard subgoals ([aristotlelib](https://pypi.org/project/aristotlelib/)).

**Phase 2 — one GPU (24–80 GB). Add a prover as a candidate generator.**
Start with the smallest thing that works: Kimina-Prover-RL-1.7B or Distill-1.7B at
**~3.4 GB bf16** (derived), 76.23% / 72.95% miniF2F-test pass@32
([blog](https://huggingface.co/blog/AI-MO/kimina-prover-rl),
[card](https://huggingface.co/AI-MO/Kimina-Prover-Distill-1.7B)) — that is a batch of 32
candidates for a fraction of a GPU-hour, and it is your cheapest sweep of the pool for
"which targets are shallow". Then Goedel-Prover-V2-8B at **~16 GB bf16** (derived) for
84.6% @32 ([paper](https://arxiv.org/pdf/2508.03613)). Both fit on a 24 GB card with room
for KV. Feed every candidate to Lean and discard failures; there is no partial credit in a
kernel.

Run the epoch loop with `lean-lsp-mcp`, whose empirical profile says `lean_local_search`
(99.5% success, 0.3 s) and `lean_run_code` (98.9%, 7.3 s) are your workhorses while
`lean_diagnostic_messages` fails 76% of the time ([slides](https://leaning.in/2026/slides/dressler.pdf)).

**Phase 3 — 2–8 GPUs. The 32B class is the sweet spot and 671B is not.**
Goedel-Prover-V2-32B and OProver-32B both need **~64 GB bf16** (derived) — one H100-80 GB
with a thin KV budget, or 2×A100-80 GB comfortably. At 4-bit that drops to **~19 GB**, and
GGUF Q4_K_M builds exist at 19.9 GB
([mradermacher](https://huggingface.co/mradermacher/Goedel-Prover-V2-32B-GGUF)). They claim
92.2% @8192 and 93.3% @32 respectively ([paper](https://arxiv.org/pdf/2508.03613),
[paper](https://arxiv.org/abs/2605.17283)). Kimina-Prover-72B at **~145 GB bf16** is an
8-GPU deployment by its own card's recommendation ([card](https://huggingface.co/AI-MO/Kimina-Prover-72B)),
or ~44 GB at 4-bit on one 80 GB card (derived).

Do **not** plan on DeepSeek-Prover-V2-671B. ~1.3 TB of bf16 weights, ~400 GB even at 4-bit
(derived), and the community reference is 16×H100-80GB for FP8 or 8×H200/8×B200
([HF forum](https://discuss.huggingface.co/t/looking-for-a-multi-gpu-server-to-run-deepseek-prover-v2-671b-can-pay/177557/2)).
Its pass@32 miniF2F number (82.4%) is below a 32B model that fits on one card
([paper](https://arxiv.org/html/2504.21801)). The scaling frontier moved.

**Quantisation.** Two things I can cite and one I cannot. I can cite that 4-bit GGUF builds
of the 32B prover exist and their sizes ([mradermacher](https://huggingface.co/mradermacher/Goedel-Prover-V2-32B-GGUF)).
I can cite that every evaluated prover loses accuracy on the ALF statement-perturbation
split, i.e. these models are sensitive to surface form
([paper](https://arxiv.org/pdf/2606.12594)). `UNVERIFIED:` I found no measurement of
quantisation's effect on Lean proof validity for any prover. Given the sensitivity above,
I would benchmark a 4-bit build against the bf16 build on 50 miniF2F problems and compare
*kernel acceptance*, not perplexity, before committing a sweep to it.

**Phase 4 — counterexample mode specifically.**
Do not run this on a prover. Run it on the strongest general reasoning model you can
afford, with (i) the informal problem statement and its references, (ii) the frozen
`Challenge.lean`, (iii) an explicit instruction to construct and *verify* a finite witness,
and (iv) an exhaustive-check program the model writes itself — which is exactly what
GPT-5.6 Pro returned to Rybin: proof certificates, an exhaustive-enumeration verification
program, machine-readable data, LaTeX source
([registry](https://whataifound.org/finding/2026-07-22-dinitz-garg-goemans)). Expect the
model to fail and need re-prompting: GPT-5.6 Pro returned nothing after 53 minutes,
nothing again after 89 more, and the counterexample came after the third push
([account](https://officechai.com/ai/mathematician-says-gpt-5-6-disproved-the-30-year-old-dinitz-garg-goemans-conjecture-with-4-simple-prompts)).
Budget hours per problem, not minutes.

Then formalise. Precedent: the Alpöge–Fable map was formalised independently in Lean 4
*after* announcement ([Zenodo](https://zenodo.org/records/21514514)); the unit-distance
disproof was formalised by a three-model ensemble over one working day
([kim-em/erdos-unit-distance](https://github.com/kim-em/erdos-unit-distance)); and the
Grasshopper case shows an Aristotle run leaving the main theorem on a `sorry` while
verifying four helper lemmas ([paper](https://arxiv.org/html/2605.20120v1)). Plan for the
formalisation to be a second project, not an afterthought — and check for `sorry` yourself.

### 5.3 A one-page decision procedure

1. Read `Challenge.lean` and the informal problem. Decide whether the frozen statement is
   faithful. If it looks degenerate, that is a defect-award play, not a bounty play — three
   of the first nine reviewed submissions went that way
   ([review decision](https://github.com/conjectures-io/conjectures-validator/blob/main/docs/review-decisions/2026-08-06-green-29.md),
   [results](https://conjectures.io/results)).
2. Search the literature for a prior proof. Ten "open" Erdős problems were already resolved
   in the literature ([paper](https://arxiv.org/pdf/2601.22401v2)), and public-source
   duplicates are disqualifying ([FAQ](https://conjectures.io/faq)).
3. If you expect a counterexample: frontier general model, hours, explicit witness,
   self-written exhaustive check, then Lean formalisation. No GPUs required.
4. If you expect a proof: agentic loop with a frontier model and `lean-lsp-mcp` first
   (Phase 1). Add a prover only when you have evidence the remaining gap is tactic-level
   rather than mathematical — and when you do, add the 8B, not the 671B.
5. Before you pay 0.5 TAO on anything: `conjectures check` clean, prelude stripped,
   `native_decide` eliminated, `#print axioms` clean, and no reference to the source theorem.
6. When your file is accepted, describe it the way Anthropic described FLT — "proved
   pending the independent re-check" until someone else has reproduced it
   ([technical note](https://www-cdn.anthropic.com/9e431dff043da6538d99d6c2d231b670aa3da263.pdf)).
   Kernel acceptance is necessary and not sufficient; the subnet says so itself, and Erdős
   726 is the proof ([FAQ](https://conjectures.io/faq),
   [results](https://conjectures.io/results/bd1a524a-c56e-42f2-9075-443df43468d7)).

---

## Appendix: claims I could not verify

- `UNVERIFIED:` the "259 audited targets / 235 Erdős / 24 Green" figure. The pinned task
  repository states 418 bundles / 209 propositions / 189 Erdős / 20 Green
  ([repo](https://github.com/conjectures-io/conjectures-tasks)).
- `UNVERIFIED:` ProofGate's full methodology and the MathOlympiadBench statement from its
  PDF — OpenReview serves a Cloudflare challenge to automated fetches. I read the ICML
  abstract and the artifact repo only.
- `UNVERIFIED:` any *independent* replication of ProofGate's Goedel-Prover-V2 finding. The
  repo is the same group's artifact release; I corroborated only the release-surface
  asymmetry (weights + training data, no benchmark proof archive).
- `UNVERIFIED:` hardware, licence and download location for Pythagoras-Prover and
  Seed-Prover weights.
- `UNVERIFIED:` how 4-bit quantisation affects Lean proof validity for any prover.
- `UNVERIFIED:` the "1.2M lines of Lean over three weeks" GPT-5.6 Sol formalisation of the
  unit-distance proof — secondary blog summary only, no primary source found.
- `UNVERIFIED:` a Lean formalisation of the Dinitz–Garg–Goemans counterexample. The
  registry grades that entry verification = *Claimed*.
- `UNVERIFIED:` Star Fleet Math's Erdős count. Its own site says 19
  ([site](https://www.starfleetmath.com/)); secondary sources say 20.
