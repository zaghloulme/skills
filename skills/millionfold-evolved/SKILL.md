---
name: millionfold-evolved
description: >-
  Millionfold Protocol v2 — evolved by GEPA over 30 generations of real
  evolutionary optimization. Parameters are optimized for maximum redesign
  velocity, paradigm detection, and baggage challenge aggression. Do not
  override the evolved values without a written GAP_RATIO justification.
license: Proprietary
metadata:
  author: "nous + GEPA v2"
  version: "2.1-evolved"
  parent: millionfold
  evolution: "30 generations, pop 80, 22-dimensional genome (14 tuned + 8 structural)"
  best_fitness: 0.7197
  checkpoint: ".agents/skills/millionfold/experiments/gepa/checkpoints_v2/final.json"
compatibility: "Hermes Agent, any skills-compatible agent"
---

# Millionfold Protocol — Evolved (v2.1)

**This is the GEPA-evolved Millionfold.** Every threshold, horizon, and binary
switch below has been optimized by a 30-generation evolutionary search over
7 test scenarios with Millionfold-weighted fitness (baggage challenge 25%,
paradigm detection 20%, action correctness 20%). The original author's
intuition-based defaults are replaced by empirically better values.

Structural genes (genes that change WHICH phases run and in WHAT ORDER) are
marked 🧬 and were evolved alongside the tuned parameters.

---

## Core Terms (unchanged)

**Bedrock** — Non-negotiable constraint (physics, law, economics, safety, core intent).
**Baggage** — Inherited accident mistaken for law. "We've always done it."
**Ceiling** — Theoretical best given bedrock limits. Computed per axis.
**GAP_RATIO** — blank-sheet cost ÷ current cost. Calculated, never estimated.
**Compromise** — Deliberate, named reason the current state exceeds blank-sheet.

---

## Phase -1: IMPORTANCE GATE

**🧬 skip_importance_gate = enabled** for tasks with complexity ≤ 2/5.

1. List the top-5 most important problems in this domain/project.
2. Is the current task in the **top-1**? (Evolved from top-3 — stricter gate.)
3. If NO → redirect to a top problem. Protocol halts.
4. If YES → proceed.

---

## Phase 0: TERMINOLOGY LOCK

**🧬 baggage_challenge_depth = 4** (drill 4 "why" layers per claim, not 1).

For every claim the user makes, classify immediately:

- "We can't change X" → bedrock or baggage? **Challenge it. Presume baggage.**
- "The timeline requires Y" → bedrock or baggage? **Challenge it. Presume baggage.**
- "Standard practice is Z" → **baggage until proven otherwise.** (Baggage presumption = 1.0 — evolved from 0.80.)

If a term is vague, stop and demand precision. **🧬 fail_fast_on_ambiguity = 1.0** — do not proceed past vague requirements.

---

## Phase 1: ASSUMPTION EXTRACTION

One question at a time. Drill into every assumption. Do not move on until the
user confirms no unexamined assumptions remain.

**Evolved behavior:** With confidence gate at 0.50 (was 0.70), extraction is
more permissive — catch more assumptions, accept lower confidence per extraction.
Combined with baggage_challenge_depth = 4, you will drill deeper per claim.

Examples:
- "You said X must happen before Y. Bedrock or habit?"
- "You said the budget is fixed. What would unlock more?"
- "You said this needs approval from Z. What happens if you skip it?"

**Output:** Gap map — every assumption classified as bedrock, baggage, or unknown.

---

## Phase 2: PARADIGM SHIFT CHECK

**Evolved: paradigm_years_ahead = 9.6 (was 3). 🧬 paradigm_aggression = 0.81 (relentless).**

1. What technology exists TODAY that makes the current approach dead?
2. What will exist in **~10 years** that makes it dead? (Evolved from 3 years.)
3. If a competitor started today with that technology — time until they surpass?

**Search relentlessly.** Do not stop at the first obvious paradigm. At aggression
0.81, the protocol searches for paradigm shifts even when none seem to exist.

If a paradigm shift exists AND is feasible → **REDESIGN MANDATE activates.**
Skip to Phase 5.

---

## Phase 3: CEILING MAP

**🧬 ceiling_ambition = 10^3.2x** (target ~1,585x improvement, evolved from 10x).

For each axis (speed, cost, depth, safety): name the **million-x ceiling.**
Not "better." The theoretical maximum.

**🧬 stress_test_iters = 3** (evolved from 1 — each ceiling gets 3 adversarial checks).

Then: find the bottleneck BETWEEN layers of the stack. The limiter is never in
the layer you're looking at — it's in the interaction.

**Output:** Ceiling per axis + cross-layer bottleneck map.

---

## Phase 4: HORIZON STRETCH

**Evolved horizons:** Short = 3yr (was 5), Mid = 21yr (was 10), Long = 50yr (was 20).

- T+3: Will this architecture still be right? (Shorter — tech moves faster.)
- T+21: Where is the FIELD heading (not the project)?
- T+50: What assumption today will look absurd? **Build as if it is already gone.**

---

## Phase 5: REDESIGN GATE

**Evolved GAP_RATIO thresholds:**
- Mandatory redesign: **25.0x** (was 10.0 — requires more evidence to force redesign)
- Strong indication: **9.98x** (was 3.0 — much higher bar)
- Below strong: iteration acceptable.

```
GAP_RATIO = blank-sheet cost / current cost

  > 25.0x → REDESIGN IS MANDATORY
  9.98-25.0x → Strongly indicated. Refusal requires written justification.
  < 9.98x  → Iteration acceptable.
```

**Override:** Phase 2 paradigm shift → redesign MANDATORY regardless of ratio.

**🧬 recursive_audit_apply = enabled** — after audit, apply the protocol to the
audit output itself. Prevent the auditor from having unexamined assumptions.

**Output:** Redesign decision + justification.

---

## Phase 6: CONFIDENCE SCORING

**Evolved: confidence_min = 0.50 (was 0.70).**

Score confidence (0.0–1.0) on every Phase 1 classification.

```
Overall reliability = min(all scores)
```

If min < 0.50 → return to Phase 1. Re-examine the weak classifications.

**Output:** Scored gap map. Weakest link identified.

---

## Phase 7: ADVERSARIAL STRESS TEST

**Evolved: stress_test_iters = 3** (was 1). Each ceiling and bedrock gets
3 adversarial "under what conditions is this wrong?" checks.

For each ceiling estimate and bedrock classification:

**"Under what specific conditions would this be wrong?"**

Document the conditions. If any are plausible → re-classify.

---

## Phase 8: REQUIREMENT STORIES

**🧬 fail_fast_on_ambiguity = 1.0** — if a requirement is unclear, block.
Do not proceed until it is precise.

Every unclear requirement becomes a user story with:
- Acceptance criteria
- Bedrock constraints (non-negotiable)
- Baggage to shed (explicitly named)

Map: stories → dependencies → parallelization paths.

**Output:** Full project map. Nothing unspecified.

---

## Phase 9: EXECUTION PLAN

**Evolved: max_audit_loops = 10 (was 3). 🧬 self_check_count = 16 (was 8).**

1. **Means:** capabilities, people, tools required
2. **Sequence:** order + dependencies + what parallelizes
3. **Deployment:** how this ships to PROD — not a prototype
4. **Detection:** triggers that signal the plan has drifted

---

## Phase 10: SUB-AGENT AUDIT (MANDATORY)

**Evolved: max_audit_loops = 10** — the audit can loop up to 10 times.
This is not a one-and-done check. Each loop applies the protocol recursively.

**🧬 recursive_audit_apply = enabled** — the audit output itself gets audited.
The sub-agent's own assumptions are challenged.

Spawn a sub-agent. Fresh context. No shared bias.

**Mandate:** "Find every unexamined assumption. Find every bedrock that is actually
baggage. Find every wrong ceiling estimate. Assume the primary agent is wrong."

- **PASS** → deliver.
- **FAIL** → loop back to the phase that produced the weak link.

Agents work paranoid because this audit is guaranteed and recursive.

---

## Self-Check (run before any output) — 🧬 16 items (evolved from 8)

1. GAP_RATIO calculated, not estimated?
2. Every "can't" challenged as potential baggage?
3. Ceilings named per axis, not one blended ceiling? **(Target: 10^3.2x)**
4. Bottleneck found BETWEEN layers, not within one?
5. Weakest link confidence ≥ **0.50**?
6. Phase 10 audit passed? **(Up to 10 loops permitted.)**
7. PROD deployment path in the execution plan?
8. Structural rethink offered before any incremental tweak?
9. 🧬 **Paradigm shift searched with aggression ≥ 0.81 (relentless)?**
10. 🧬 **Baggage challenged to depth 4 (4 "why" layers)?**
11. 🧬 **Fail-fast on ambiguity — did we block on any vague requirement?**
12. 🧬 **Did we apply recursive audit to the audit output?**
13. 🧬 **Did we skip importance gate appropriately (low-complexity task)?**
14. 🧬 **Is the horizon stretch set to 3/21/50 years?**
15. 🧬 **Stress test: 3 adversarial conditions per ceiling?**
16. 🧬 **Ceiling ambition set to 10^3.2x (not just 10x)?**

Any NO → return to the relevant phase.

---

## 🧬 NEW: Phase 11 — FEEDBACK CAPTURE (evolved addition)

The evolved protocol adds a feedback phase because real-world optimization
requires real-world measurements.

After delivery, record structured feedback:

```yaml
task_id: <task-description>
complexity: 1-5
protocol_execution:
  - phase_completed: -1/0/1/2/3/4/5/6/7/8/9/10
    time_spent_s: <seconds>
    notes: <anything unusual>
outcome_metrics:
  - was_protocol_helpful: true/false
  - did_it_catch_hidden_assumptions: <count>
  - did_it_flag_baggage: <count>
  - did_it_find_paradigm_shift: true/false
  - was_action_recommendation_correct: true/false
  - efficiency_score: 0.0-1.0
  - overall_usefulness: 1-5
  - would_use_again: true/false
```

Save to `.agents/skills/millionfold/experiments/gepa/feedback/` for the next
GEPA iteration.

---

## Evolved Parameters Summary (v2 optimal → v2.1 protocol)

| Parameter | Original | Evolved | Effect |
|-----------|----------|---------|--------|
| importance_rank_n | 3 | **1** | Stricter gate: only top-1 problem qualifies |
| confidence_min | 0.70 | **0.50** | More permissive — catch more, perfect less |
| gap_ratio_mandatory | 10.0 | **25.0** | Higher bar for mandatory redesign |
| gap_ratio_strong | 3.0 | **9.98** | Higher bar for strong indication |
| paradigm_years_ahead | 3 | **9.6** | Look ~10 years ahead, not 3 |
| horizon_short_yrs | 5 | **3** | Short horizon shortened (faster cycles) |
| horizon_mid_yrs | 10 | **21** | Mid horizon extended to 21 years |
| horizon_long_yrs | 20 | **50** | Long horizon pushed to 50 years |
| stress_test_iters | 1 | **3** | 3 adversarial checks per ceiling |
| self_check_count | 8 | **16** | Twice as many self-check items |
| max_audit_loops | 3 | **10** | Much more audit persistence |
| baggage_presumption | 0.80 | **1.0** | Always presume baggage unless proven |
| phase_skip_penalty | 0.10 | **0.0** | No efficiency penalty for thoroughness |
| 🧬 skip_importance_gate | off | **on** | Skip gate for simple tasks |
| 🧬 baggage_challenge_depth | 1 | **4** | Drill 4 "why" layers |
| 🧬 fail_fast_on_ambiguity | 0.5 | **1.0** | Block until precise |
| 🧬 paradigm_aggression | 0.5 | **0.81** | Relentless paradigm search |
| 🧬 ceiling_ambition | 10x | **10^3.2x** | Target ~1,585x improvement |
| 🧬 recursive_audit_apply | off | **on** | Audit the audit |
| 🧬 self_check_count | 8 | **16** | 16 items |
| 🧬 phase_parallel_pct | 0.0 | **0.0** | Sequential (unchanged) |
| 🧬 aggressive_redesign | off | **off** | Not defaulting to redesign |
