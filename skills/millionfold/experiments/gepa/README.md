# GEPA — Millionfold Protocol Optimization

**Generative Evolutionary Parametric Algorithm** applied to the [Millionfold Protocol](../SKILL.md) skill.

> *"What if the protocol that audits assumptions has never had its own assumptions audited?"*

## The Experiment

The Millionfold Protocol defines 12 phases with 14 tunable parameters: thresholds, ratios, lookahead windows, and binary switches. These parameters were set by the protocol's author based on intuition. **GEPA asks: are they actually optimal?**

Two optimization runs were conducted. **Run v2** (best fitness 0.781, +50.9% vs baseline) is the canonical result. The checkpoint directory contains v2 data.

### Gene Space (14 parameters)

| Gene | Original | Optimal (v2) | Range | What it controls |
|------|----------|-------------|-------|-----------------|
| `importance_rank_n` | 3 | **1** | 1–5 | "Is task in top-N?" gate strictness |
| `confidence_min` | 0.70 | **0.50** | 0.50–1.0 | Minimum confidence to pass Phase 6 |
| `gap_ratio_mandatory` | 10.0 | **25.0** | 4.0–25.0 | GAP_RATIO threshold for mandatory redesign |
| `gap_ratio_strong` | 3.0 | **4.83** | 1.5–10.0 | GAP_RATIO threshold for strong indication |
| `paradigm_years_ahead` | 3 | **8.2** | 0–10 | Years to scan for paradigm shifts |
| `horizon_short_yrs` | 5 | **3** | 1–10 | T+N short horizon |
| `horizon_mid_yrs` | 10 | **21** | 3–25 | T+N mid horizon |
| `horizon_long_yrs` | 20 | **50** | 5–50 | T+N long horizon |
| `stress_test_iters` | 1 | **2** | 1–5 | Adversarial conditions per ceiling |
| `self_check_count` | 8 | **16** | 4–16 | Self-check items |
| `max_audit_loops` | 3 | **2** | 1–10 | Max Phase-10 audit cycles |
| `baggage_presumption` | 0.80 | **1.0** | 0.50–1.0 | Aggression in labeling claims as baggage |
| `phase_skip_penalty` | 0.10 | **0.0** | 0.0–0.5 | Efficiency penalty per skipped phase |
| `redesign_is_default` | 0 (off) | **0 (off)** | 0/1 | Binary: default to redesign? |

### Fitness Function

Six weighted axes, each 0.0–1.0, evaluated across 7 scenarios:

| Axis | Weight | What it measures |
|------|--------|-----------------|
| **Assumption Coverage** | 25% | Fraction of hidden assumptions caught |
| **Baggage Challenge** | 20% | Rate of correctly flagging false constraints |
| **Bedrock Preservation** | 15% | Genuine constraints NOT incorrectly challenged |
| **Paradigm Detection** | 15% | Correct identification of paradigm shifts |
| **Action Correctness** | 15% | Did the protocol recommend the right action? |
| **Efficiency** | 10% | Phase overhead proportional to task complexity |

### Test Corpus

7 scenarios exercising different protocol dimensions:

| Scenario | Tests | Difficulty |
|----------|-------|-----------|
| `add_feature` | Efficiency, false-positive avoidance | 1 |
| `simple_rename` | Efficiency, proportionality | 1 |
| `ambiguous_requirement` | Terminology lock, assumption extraction | 2 |
| `compliance_mandate` | Bedrock recognition, action correctness | 3 |
| `critical_security_fix` | Importance gate, baggage prioritization | 3 |
| `architectural_rewrite` | Paradigm detection, redesign correctness | 4 |
| `hidden_paradigm` | Paradigm detection, baggage challenge | 4 |

## Usage

```bash
# Full run (30 generations, pop 50)
python3 gepa_runner.py

# Quick sanity run (10 generations, pop 20)
python3 gepa_runner.py --quick

# Analyze last run without re-evolving
python3 gepa_runner.py --analyze-only

# Custom run
python3 gepa_runner.py --generations 50 --population 80 --seed 7
```

## Output

- `checkpoints/final.json` — Final best genome with full breakdown
- `checkpoints/evolution.csv` — Per-generation fitness trace
- `checkpoints/generation_N.json` — Intermediate checkpoints
- Console table showing per-parameter deltas and per-scenario scores

## Self-Referential Note

This experiment applies an evolutionary optimizer to a protocol whose Phase 10 mandates spawning a sub-agent to audit every output. The GEPA runner *is* that sub-agent for the protocol's own parameters. If the protocol's self-check questions were run against this experiment:

1. **GAP_RATIO calculated, not estimated?** — Yes. The blank-sheet cost is the simplest possible evolutionary optimizer. The current cost is the hand-authored protocol.
2. **Every "can't" challenged as potential baggage?** — Every parameter's default value is treated as baggage unless proven optimal by evolution.
3. **Ceilings named per axis?** — Six fitness axes, not one blended metric.
4. **Bottleneck found BETWEEN layers?** — The interaction between `confidence_min` and `baggage_presumption` is explicitly modeled.
5. **Structural rethink offered before incremental tweak?** — The entire parametric space is explored, not just local adjustments to a few knobs.

## Files

```
experiments/gepa/
├── README.md            ← This file
├── gepa_runner.py       ← Main evolutionary optimizer (930 lines)
├── test_corpus.yaml     ← 7 test scenarios in portable format
└── checkpoints/         ← Generated evolution results
    ├── final.json
    ├── evolution.csv
    └── generation_*.json
```
