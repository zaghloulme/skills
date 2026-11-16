---
name: millionfold
description: >-
  Enforced long-horizon reasoning protocol. Use before any planning, strategy,
  or implementation. Extracts all assumptions, calculates ceilings, mandates
  redesign when warranted, and audits every output through an adversarial
  sub-agent. Always apply — never skip.
license: Proprietary
metadata:
  author: nous
  version: "2.0"
compatibility: "Hermes Agent, any skills-compatible agent"
---

# Millionfold Protocol

Enforced sequential protocol. Do not skip phases. Do not proceed until each phase produces its output.

## Core Terms

**Bedrock** — Non-negotiable constraint (physics, law, economics, safety, core intent).
**Baggage** — Inherited accident mistaken for law. "We've always done it."
**Ceiling** — Theoretical best given bedrock limits. Computed per axis (speed, cost, depth, safety).
**GAP_RATIO** — blank-sheet cost ÷ current cost. Calculated, never estimated.
**Compromise** — Deliberate, named reason the current state exceeds blank-sheet.

---

## Phase -1: IMPORTANCE GATE

1. List the top-5 most important problems in this domain/project.
2. Is the current task in the top-3?
3. If NO → redirect to a top-3 problem. Protocol halts.
4. If YES → proceed.

---

## Phase 0: TERMINOLOGY LOCK

For every claim the user makes, classify immediately:

- "We can't change X" → bedrock or baggage? Challenge it.
- "The timeline requires Y" → bedrock or baggage? Challenge it.
- "Standard practice is Z" → baggage until proven otherwise.

If a term is vague, stop and demand precision. "You said 'hard to change' — bedrock or baggage? They are different."

---

## Phase 1: ASSUMPTION EXTRACTION

One question at a time. Drill into every assumption. Do not move on until the user confirms no unexamined assumptions remain.

Examples:
- "You said X must happen before Y. Bedrock or habit?"
- "You said the budget is fixed. What would unlock more?"
- "You said this needs approval from Z. What happens if you skip it?"

**Output:** Gap map — every assumption classified as bedrock, baggage, or unknown, with one-sentence rationale each.

---

## Phase 2: PARADIGM SHIFT CHECK

1. What technology exists TODAY that makes the current approach dead?
2. What will exist in 3 years that makes it dead?
3. If a competitor started today with that technology — time until they surpass?

If a paradigm shift exists AND is feasible → **REDESIGN MANDATE activates.** Skip to Phase 5.

---

## Phase 3: CEILING MAP

For each axis (speed, cost, depth, safety): name the **1,000,000x ceiling.** Not "better." The theoretical maximum.

Then: find the bottleneck BETWEEN layers of the stack. The limiter is never in the layer you're looking at — it's in the interaction.

**Output:** Ceiling per axis + cross-layer bottleneck map.

---

## Phase 4: HORIZON STRETCH

- T+5: Will this architecture still be right?
- T+10: Where is the FIELD heading (not the project)?
- T+20: What assumption today will look absurd? **Build as if it is already gone.**

---

## Phase 5: REDESIGN GATE

```
GAP_RATIO = blank-sheet cost / current cost

  > 10x   → REDESIGN IS MANDATORY
  3-10x   → Strongly indicated. Refusal requires written justification.
  < 3x    → Iteration acceptable.
```

**Override:** Phase 2 paradigm shift → redesign MANDATORY regardless of ratio.

**Output:** Redesign decision + justification.

---

## Phase 6: CONFIDENCE SCORING

Score confidence (0.0–1.0) on every Phase 1 classification.

```
Overall reliability = min(all scores)
```

If min < 0.7 → return to Phase 1. Re-examine the weak classifications.

**Output:** Scored gap map. Weakest link identified.

---

## Phase 7: ADVERSARIAL STRESS TEST

For each ceiling estimate and bedrock classification:

**"Under what specific conditions would this be wrong?"**

Document the conditions. If any are plausible → re-classify.

---

## Phase 8: REQUIREMENT STORIES

Every unclear requirement becomes a user story with:
- Acceptance criteria
- Bedrock constraints (non-negotiable)
- Baggage to shed (explicitly named)

Map: stories → dependencies → parallelization paths.

**Output:** Full project map. Nothing unspecified.

---

## Phase 9: EXECUTION PLAN

1. **Means:** capabilities, people, tools required
2. **Sequence:** order + dependencies + what parallelizes
3. **Deployment:** how this ships to PROD — not a prototype
4. **Detection:** triggers that signal the plan has drifted

---

## Phase 10: SUB-AGENT AUDIT (MANDATORY)

Spawn a sub-agent. Fresh context. No shared bias.

**Mandate:** "Find every unexamined assumption. Find every bedrock that is actually baggage. Find every wrong ceiling estimate. Assume the primary agent is wrong."

- **PASS** → deliver.
- **FAIL** → loop back to the phase that produced the weak link.

Agents work paranoid because this audit is guaranteed.

---

## Self-Check (run before any output)

1. GAP_RATIO calculated, not estimated?
2. Every "can't" challenged as potential baggage?
3. Ceilings named per axis, not one blended ceiling?
4. Bottleneck found BETWEEN layers, not within one?
5. Weakest link confidence ≥ 0.7?
6. Phase 10 audit passed?
7. PROD deployment path in the execution plan?
8. Structural rethink offered before any incremental tweak?

Any NO → return to the relevant phase.


