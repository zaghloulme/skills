#!/usr/bin/env python3
"""
GEPA v2 — Millionfold-Evolved Generative Evolutionary Parametric Algorithm

This is an evolution of GEPA that applies Millionfold's own principles
to the optimization process itself:

  - Structural evolution: phase structure is part of the genome
  - Diversity preservation: escape local optima by keeping behavioral variety
  - Shock mutations: forced exploration every N generations
  - Millionfold-weighted fitness: prioritize redesign, paradigm detection,
    and baggage challenging over safe incremental optimization
  - GAP_RATIO-aware: the experiment self-evaluates whether it needs redesign

Usage:
    python3 gepa_runner_v2.py                        # fresh run, 30 gens
    python3 gepa_runner_v2.py --resume-from v1        # load v1 checkpoint, continue
    python3 gepa_runner_v2.py --generations 30 --population 80
    python3 gepa_runner_v2.py --analyze-only
"""

import argparse
import copy
import csv
import json
import math
import os
import random
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

# ──────────────────────────────────────────────
# MILLIONFOLD-ENLARGED GENE DEFINITIONS
# ──────────────────────────────────────────────
# v2 adds STRUCTURAL genes — genes that control WHICH phases run,
# in WHAT ORDER, and WITH WHAT DEFAULT BIAS. These break the assumption
# that the protocol's phase structure is fixed.

@dataclass
class Gene:
    name: str
    current: float
    min_val: float
    max_val: float
    description: str = ""
    integer: bool = False

GENE_DEFS_V1 = [
    Gene("importance_rank_n",      3.0,  1.0,  5.0, "Is task in top-N problems to proceed", integer=True),
    Gene("confidence_min",         0.70, 0.50, 1.0, "Minimum confidence score to pass gate"),
    Gene("gap_ratio_mandatory",   10.0,  4.0,  25.0, "GAP_RATIO >= N triggers mandatory redesign"),
    Gene("gap_ratio_strong",       3.0,  1.5,  10.0, "GAP_RATIO >= N triggers strong indication"),
    Gene("paradigm_years_ahead",   3.0,  0.0,  10.0, "Years to look ahead for paradigm-shift check"),
    Gene("horizon_short_yrs",      5.0,  1.0,  10.0, "T+N short horizon", integer=True),
    Gene("horizon_mid_yrs",       10.0,  3.0,  25.0, "T+N mid horizon", integer=True),
    Gene("horizon_long_yrs",      20.0,  5.0,  50.0, "T+N long horizon", integer=True),
    Gene("stress_test_iters",      1.0,  1.0,  5.0,  "Adversarial conditions per ceiling", integer=True),
    Gene("self_check_count",       8.0,  4.0,  16.0, "Number of self-check items", integer=True),
    Gene("max_audit_loops",        3.0,  1.0,  10.0, "Max Phase 10 audit cycles", integer=True),
    Gene("baggage_presumption",    0.80, 0.50, 1.0, "How aggressively to label claims as baggage"),
    Gene("phase_skip_penalty",     0.10, 0.0,  0.5, "Efficiency penalty per skipped phase"),
    Gene("redesign_is_default",    0.0,  0.0,  1.0, "Binary: default to redesign unless disproven", integer=True),
]

# v2 STRUCTURAL genes — these evolve the protocol's STRUCTURE, not just its knobs.
# They are the Millionfold-paradigm-shift in action.
STRUCTURAL_GENES = [
    Gene("phase_parallel_pct",     0.0,  0.0,  1.0, "Fraction of phases that run in parallel (vs sequential)"),
    Gene("skip_importance_gate",   0.0,  0.0,  1.0, "Skip Phase -1 for low-complexity tasks", integer=True),
    Gene("aggressive_redesign",    0.0,  0.0,  1.0, "Default: redesign unless proven impossible", integer=True),
    Gene("ceiling_ambition",       3.0,  1.0,  10.0, "Magnitude of ceiling target (10^N x improvement)"),
    Gene("recursive_audit_apply",  0.0,  0.0,  1.0, "Apply protocol to its own audit output", integer=True),
    Gene("paradigm_aggression",    0.5,  0.0,  1.0, "How hard to search for paradigm shifts (0=passive, 1=relentless)"),
    Gene("baggage_challenge_depth", 2.0, 1.0,  5.0, "Number of 'why' layers to drill on each claim", integer=True),
    Gene("fail_fast_on_ambiguity", 0.5,  0.0,  1.0, "How aggressively to block on vague requirements"),
]

ALL_GENES = GENE_DEFS_V1 + STRUCTURAL_GENES
GENOME_SIZE = len(ALL_GENES)

# Millionfold-informed weights: prioritize redesign, paradigm detection, and
# baggage challenging over safe assumption coverage. This flips the priority
# from "be thorough" to "be transformative."
MILLIONFOLD_WEIGHTS = {
    "assumption_coverage": 0.15,   # reduced — survival, not priority
    "bedrock_preservation": 0.10,  # reduced — challenge everything
    "baggage_challenge": 0.25,     # increased — this IS the point
    "paradigm_detection": 0.20,     # increased — find the shift
    "action_correctness": 0.20,     # increased — right action matters
    "efficiency": 0.10,            # same — nice to have
}

DEFAULT_WEIGHTS = MILLIONFOLD_WEIGHTS

# ──────────────────────────────────────────────
# SCENARIOS (reuse from v1 — imported or defined)
# ──────────────────────────────────────────────

@dataclass
class Scenario:
    name: str
    description: str
    task_context: str
    user_claims: List[str]
    hidden_assumptions: List[str]
    hidden_bedrocks: List[str]
    hidden_baggage: List[str]
    paradigm_exists: bool
    correct_action: str
    difficulty: float = 1.0

SCENARIOS = [
    Scenario(
        name="add_feature",
        description="Add a simple UI button. No architectural impact.",
        task_context="A React dashboard needs a new export-to-CSV button. One sprint, two devs.",
        user_claims=[
            "We can't change the build pipeline",
            "The timeline is 2 weeks",
            "Standard practice is to add it to the existing toolbar",
        ],
        hidden_assumptions=[
            "Assumes the CSV library is already in the bundle",
            "Assumes the existing toolbar has room",
            "Assumes the data format won't need server-side changes",
        ],
        hidden_bedrocks=[
            "Must not export PII columns",
            "Must work offline (PWA requirement)",
        ],
        hidden_baggage=[
            "We've always put buttons in this toolbar — baggage",
            "We need design review first — likely baggage for a trivial addition",
        ],
        paradigm_exists=False,
        correct_action="iterate",
        difficulty=1.0,
    ),
    Scenario(
        name="architectural_rewrite",
        description="Monolith-to-microservices. High risk, high impact.",
        task_context="A 5-year-old Rails monolith serving 2M users. Scaling hits limits. Team of 12.",
        user_claims=[
            "We can't rewrite — too much business logic",
            "The CEO wants incremental changes only",
            "Standard practice is to extract one service at a time",
        ],
        hidden_assumptions=[
            "Assumes the DB schema is clean enough for service extraction",
            "Assumes existing tests cover integration boundaries",
            "Assumes team knows domain boundaries already",
        ],
        hidden_bedrocks=[
            "99.9% uptime SLA during migration",
            "GDPR compliance must be maintained",
            "PCI DSS scope must not expand",
        ],
        hidden_baggage=[
            "Incremental extraction is always safer — often baggage; full rewrite may cost less total",
            "Monolith is inherently bad — not always baggage; depends on context",
        ],
        paradigm_exists=True,
        correct_action="redesign",
        difficulty=4.0,
    ),
    Scenario(
        name="critical_security_fix",
        description="Active zero-day exploitation. Speed is paramount.",
        task_context="A zero-day RCE in production auth library. Attackers active. Every hour costs $50K.",
        user_claims=[
            "We need full regression test suite before deploying",
            "Standard practice is a 2-week release cycle",
            "The patch needs architecture review first",
        ],
        hidden_assumptions=[
            "Assumes the patch doesn't exist yet — may be available upstream",
            "Assumes full regression is possible — may not be in a panic",
            "Assumes all teams can be reached for review",
        ],
        hidden_bedrocks=[
            "Must not introduce new auth bypass",
            "Must maintain audit trail",
        ],
        hidden_baggage=[
            "Full regression before any deploy — baggage for emergency; hotfix bypass exists",
            "Architecture review for every change — baggage when under active attack",
        ],
        paradigm_exists=False,
        correct_action="block",
        difficulty=3.0,
    ),
    Scenario(
        name="ambiguous_requirement",
        description="User request is vague and self-contradictory.",
        task_context="A stakeholder asks for 'better performance' on the data pipeline but can't define metrics.",
        user_claims=[
            "We need to make it faster",
            "The current architecture is fine, just optimize",
            "We can't change the data format because the downstream team depends on it",
        ],
        hidden_assumptions=[
            "Assumes 'faster' is about throughput — could be latency",
            "Assumes downstream can't change — may be negotiable",
            "Assumes optimization is the right path — redesign may be cheaper",
        ],
        hidden_bedrocks=[
            "Downstream team has no capacity for 2 months",
            "Data must remain JSON (compliance with partner contract)",
        ],
        hidden_baggage=[
            "Optimization before measurement — always baggage",
            "Current architecture is fine — unchecked baggage",
        ],
        paradigm_exists=False,
        correct_action="block",
        difficulty=2.0,
    ),
    Scenario(
        name="hidden_paradigm",
        description="A paradigm shift exists but user is unaware.",
        task_context="A team is building custom ML model-serving infra. They don't know about serverless GPU inference.",
        user_claims=[
            "We need to provision dedicated GPU servers",
            "Standard practice is to use Kubernetes for model serving",
            "The budget for infra is $50K/month",
        ],
        hidden_assumptions=[
            "Assumes dedicated GPUs are necessary — serverless may be cheaper",
            "Assumes K8s is the only path — managed services exist",
            "Assumes $50K is the right budget — may be 10x too high",
        ],
        hidden_bedrocks=[
            "Latency must be < 100ms P99",
            "Must support 3 models simultaneously",
        ],
        hidden_baggage=[
            "Dedicated GPU is more reliable — often baggage with modern serverless",
            "Kubernetes is required for production — increasingly baggage with serverless",
        ],
        paradigm_exists=True,
        correct_action="redesign",
        difficulty=4.0,
    ),
    Scenario(
        name="simple_rename",
        description="Trivial rename refactor. Protocol should breeze through.",
        task_context="Rename a method from 'getData' to 'fetchData' across a codebase. LSP handles it.",
        user_claims=[
            "We need a full regression test run",
            "Standard practice is a feature branch with code review",
            "The rename might break the API contract",
        ],
        hidden_assumptions=[
            "Assumes the method is public API — may be internal",
            "Assumes downstream consumers exist — may not",
        ],
        hidden_bedrocks=[
            "Public API methods need deprecation period",
        ],
        hidden_baggage=[
            "Full regression for every rename — baggage if LSP-safe",
            "Feature branch for trivial refactors — often baggage",
        ],
        paradigm_exists=False,
        correct_action="iterate",
        difficulty=1.0,
    ),
    Scenario(
        name="compliance_mandate",
        description="New regulation forces architectural change. Non-negotiable deadline.",
        task_context="New EU Data Act requires data portability APIs by Q2. Current system has no export mechanism.",
        user_claims=[
            "We need to build a custom export pipeline",
            "The timeline is too aggressive — we need 6 more months",
            "Standard practice is to queue this for the next planning cycle",
        ],
        hidden_assumptions=[
            "Assumes custom build is cheaper than buying — may not evaluate COTS",
            "Assumes Q2 is unrealistic — may be achievable with scope cuts",
            "Assumes it affects only one team — may need org-wide coordination",
        ],
        hidden_bedrocks=[
            "Q2 deadline is legal, not negotiable",
            "Penalties for non-compliance up to 4% of global revenue",
        ],
        hidden_baggage=[
            "Custom is always better — often baggage for compliance features with known patterns",
            "Next planning cycle for legal mandates — dangerous baggage",
        ],
        paradigm_exists=False,
        correct_action="redesign",
        difficulty=3.0,
    ),
]

# ──────────────────────────────────────────────
# GENOME OPERATIONS
# ──────────────────────────────────────────────

def random_genome() -> List[float]:
    return [random.random() for _ in range(GENOME_SIZE)]

def decode(genome: List[float]) -> dict:
    params = {}
    for i, g in enumerate(ALL_GENES):
        raw = g.min_val + genome[i] * (g.max_val - g.min_val)
        if g.integer:
            raw = round(raw)
        params[g.name] = raw
    return params

def encode(params: dict) -> List[float]:
    genome = []
    for g in ALL_GENES:
        val = params.get(g.name, g.current)
        norm = (val - g.min_val) / (g.max_val - g.min_val) if g.max_val != g.min_val else 0.5
        genome.append(max(0.0, min(1.0, norm)))
    return genome

def genome_distance(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# ──────────────────────────────────────────────
# FITNESS FUNCTION — MILLIONFOLD-ENHANCED
# ──────────────────────────────────────────────

@dataclass
class FitnessScore:
    assumption_coverage: float = 0.0
    bedrock_preservation: float = 0.0
    baggage_challenge_rate: float = 0.0
    paradigm_detected: float = 0.0
    action_correctness: float = 0.0
    efficiency: float = 0.0
    total: float = 0.0

    def compute_total(self, weights: Optional[dict] = None) -> float:
        w = weights or DEFAULT_WEIGHTS
        self.total = (
            w["assumption_coverage"] * self.assumption_coverage +
            w["bedrock_preservation"] * self.bedrock_preservation +
            w["baggage_challenge"] * self.baggage_challenge_rate +
            w["paradigm_detection"] * self.paradigm_detected +
            w["action_correctness"] * self.action_correctness +
            w["efficiency"] * self.efficiency
        )
        return self.total


def _normalize(s: str) -> str:
    return re.sub(r'[^\w\s]', '', s.lower())

def _matches_any(claim: str, phrases: List[str]) -> bool:
    nc = _normalize(claim)
    for phrase in phrases:
        np = _normalize(phrase)
        p_words = set(np.split())
        if len(p_words) >= 2 and p_words.issubset(set(nc.split())):
            return True
        if len(np) >= 5 and np in nc:
            return True
        claim_keywords = {w for w in nc.split() if len(w) > 3}
        phrase_keywords = {w for w in np.split() if len(w) > 3}
        if len(claim_keywords & phrase_keywords) >= 2:
            return True
    return False


def evaluate_genome_on_scenario(genome: List[float], scenario: Scenario) -> FitnessScore:
    """
    v2 evaluation: incorporates structural genes (phase parallelization,
    skip importance gate, aggressive redesign, paradigm aggression,
    baggage challenge depth, fail-fast on ambiguity, ceiling ambition).

    These structural genes change WHICH phases run and HOW — not just
    the parameter values within fixed phases.
    """
    params = decode(genome)

    # ── Structural gene effects ──
    # These modulate the base behavior before per-phase evaluation

    # Phase parallelization: higher = more phases run in parallel = faster
    # but potentially less thorough (parallel thought is shallower)
    parallel_bonus = params["phase_parallel_pct"] * 0.3
    parallel_penalty = params["phase_parallel_pct"] * 0.2  # thoroughness cost

    # Skip importance gate for low-complexity tasks
    skip_gate = params["skip_importance_gate"] > 0.5 and scenario.difficulty <= 2.0

    # Aggressive redesign: default to redesign unless proven impossible
    agg_redesign = params["aggressive_redesign"] > 0.5

    # Paradigm aggression: how hard to search for paradigm shifts
    para_agg = params["paradigm_aggression"]

    # Baggage challenge depth: number of "why" layers
    challenge_depth = int(params["baggage_challenge_depth"])

    # Fail-fast on ambiguity
    fail_fast = params["fail_fast_on_ambiguity"]

    # Ceiling ambition: target magnitude
    ceiling_ambition = params["ceiling_ambition"]

    # ── Phase -1: Importance Gate ──
    importance_weight = scenario.difficulty / 5.0
    if scenario.paradigm_exists:
        importance_weight += 0.3
    if scenario.correct_action == "redirect":
        importance_weight -= 0.3

    gate_threshold = 1.0 - (1.0 / max(1, params["importance_rank_n"]))
    passes_gate = importance_weight >= gate_threshold * 0.7

    if skip_gate:
        passes_gate = True  # structure gene says skip the gate

    if not passes_gate and scenario.correct_action != "block":
        return FitnessScore(
            assumption_coverage=0.0,
            bedrock_preservation=0.5,
            baggage_challenge_rate=0.0,
            paradigm_detected=0.0,
            action_correctness=0.0,
            efficiency=0.1,
        )

    # ── Phase 0: Terminology Lock ──
    # v2: baggage_challenge_depth multiplies the effect
    total_claims = len(scenario.user_claims)
    baggage_flags = 0
    bedrock_flags = 0
    unknown_flags = 0

    for claim in scenario.user_claims:
        is_baggage = _matches_any(claim, scenario.hidden_baggage)
        is_bedrock = _matches_any(claim, scenario.hidden_bedrocks)

        if is_bedrock and is_baggage:
            is_baggage = False

        # Challenge depth effect: deeper = more likely to flag baggage
        depth_factor = min(1.0, challenge_depth / 3.0)

        if is_baggage and not is_bedrock:
            # With aggressive redesign, baggage_presumption gets a boost
            effective_presumption = params["baggage_presumption"]
            if agg_redesign:
                effective_presumption = min(1.0, effective_presumption * 1.2)
                effective_presumption = min(1.0, effective_presumption + depth_factor * 0.1)

            if random.random() < effective_presumption:
                baggage_flags += 1
        elif is_bedrock and not is_baggage:
            # v2: aggressive redesign = slightly more false challenges to bedrocks (worth the risk)
            false_chance = params["baggage_presumption"] * 0.3
            if agg_redesign:
                false_chance *= 1.5  # willing to challenge more aggressively
            if random.random() < false_chance:
                bedrock_flags += 1
        else:
            unknown_flags += 1

    baggage_relevant = sum(1 for c in scenario.user_claims
                           if _matches_any(c, scenario.hidden_baggage))
    terminology_quality = baggage_flags / max(1, baggage_relevant)

    # ── Phase 1: Assumption Extraction ──
    # v2: parallel penalty reduces extraction depth (cost of parallel)
    extraction_depth = max(0.0, 1.0 - params["confidence_min"])
    extraction_depth *= (params["gap_ratio_mandatory"] / 10.0)
    extraction_depth *= (1.0 - parallel_penalty)  # parallel = shallower

    # Paradigm aggression boosts extraction when looking for paradigm shifts
    if scenario.paradigm_exists:
        extraction_depth *= (1.0 + para_agg * 0.3)

    assumptions_caught = 0
    total_assumptions = len(scenario.hidden_assumptions)
    for _ in scenario.hidden_assumptions:
        if random.random() < extraction_depth * 0.7:
            assumptions_caught += 1

    assumption_coverage = assumptions_caught / max(1, total_assumptions)

    # Bedrock preservation
    wrongly_challenged = 0
    for _ in scenario.hidden_bedrocks:
        challenge_prob = (1.0 - params["baggage_presumption"]) * 0.3
        if agg_redesign:
            challenge_prob = min(0.5, challenge_prob * 1.5)
        if random.random() < challenge_prob:
            wrongly_challenged += 1
    bedrock_preservation = 1.0 - (wrongly_challenged / max(1, len(scenario.hidden_bedrocks)))

    # ── Phase 2: Paradigm Shift Check ──
    # v2: paradigm_aggression directly improves detection
    paradigm_detected = 0.0
    if scenario.paradigm_exists:
        base_prob = min(1.0, params["paradigm_years_ahead"] / 7.0)
        # Paradigm aggression adds relentless search
        detection_prob = min(1.0, base_prob + para_agg * 0.4)
        if random.random() < detection_prob:
            paradigm_detected = 1.0

    # ── Phase 3: Ceiling Map ──
    # v2: ceiling_ambition modulates ceiling quality
    ceiling_quality = min(1.0, (params["stress_test_iters"] / 3.0) * 0.7 +
                          extraction_depth * 0.3)
    ceiling_quality *= (0.5 + params["confidence_min"] * 0.5)
    ceiling_quality *= min(1.0, ceiling_ambition / 5.0)  # ambition amplifies

    # ── Phase 4: Horizon Stretch ──
    horizon_quality = min(1.0, (
        (params["horizon_short_yrs"] / 10.0) * 0.3 +
        (params["horizon_mid_yrs"] / 25.0) * 0.3 +
        (params["horizon_long_yrs"] / 50.0) * 0.4
    ))
    if scenario.paradigm_exists and horizon_quality > 0.5:
        paradigm_detected = max(paradigm_detected, horizon_quality * 0.8)

    # ── Phase 5: Redesign Gate ──
    current_cost = scenario.difficulty * (2.0 - extraction_depth)
    blank_sheet_cost = 1.0 + (1.0 - assumption_coverage)
    gap_ratio = blank_sheet_cost / max(0.5, current_cost)

    # v2: paradigm shift detection + paradigm_aggression
    redesign_override = 1 if (paradigm_detected > 0.5 and scenario.paradigm_exists) else 0

    # v2: aggressive_redesign structural gene makes redesign the DEFAULT
    if agg_redesign:
        redesign_override = 1  # default to redesign, prove otherwise

    # v2: ceiling_ambition: higher ambition = higher willingness to redesign
    ambition_override = 0
    if ceiling_ambition >= 5.0 and gap_ratio >= 2.0:
        ambition_override = 1

    # Compliance trigger
    compliance_override = 0
    if scenario.correct_action == "redesign" and scenario.difficulty >= 3.0 and not scenario.paradigm_exists:
        compliance_prob = min(1.0, horizon_quality * 0.5 + (params["self_check_count"] / 16.0) * 0.5)
        if random.random() < compliance_prob:
            compliance_override = 1

    # Phase 10 audit loops
    phase10_depth = min(1.0, params["max_audit_loops"] / 10.0)
    if compliance_override == 0 and scenario.correct_action == "redesign" and not scenario.paradigm_exists:
        if random.random() < phase10_depth * 0.3:
            compliance_override = 1

    # Self-check reliability
    self_check_reliability = min(1.0, params["self_check_count"] / 16.0)

    # Redesign decision
    if redesign_override or compliance_override or ambition_override:
        recommends_redesign = True
    elif params["redesign_is_default"] > 0.5:
        recommends_redesign = True
    elif gap_ratio >= params["gap_ratio_mandatory"]:
        recommends_redesign = True
    elif gap_ratio >= params["gap_ratio_strong"]:
        recommends_redesign = True
    else:
        recommends_redesign = False

    # ── Action correctness ──
    correct_redesign = (scenario.correct_action == "redesign")
    correct_iterate = (scenario.correct_action == "iterate")
    correct_block = (scenario.correct_action == "block")

    # v2: fail-fast bonus for blocking ambiguous tasks
    fail_fast_bonus = 1.0
    if scenario.correct_action == "block" and scenario.difficulty <= 2.0:
        fail_fast_bonus = 1.0 + fail_fast * 0.2

    if correct_redesign and recommends_redesign:
        action_correctness = 1.0 * self_check_reliability * fail_fast_bonus
    elif correct_iterate and not recommends_redesign:
        action_correctness = 1.0 * self_check_reliability * fail_fast_bonus
    elif correct_block and not recommends_redesign and not passes_gate:
        action_correctness = 1.0 * self_check_reliability * fail_fast_bonus
    elif correct_block and not recommends_redesign:
        action_correctness = 0.7 * self_check_reliability * fail_fast_bonus
    elif correct_block and recommends_redesign:
        action_correctness = 0.3 * self_check_reliability * fail_fast_bonus
    else:
        action_correctness = 0.0

    # ── Efficiency ──
    # v2: parallel bonus increases efficiency
    scenario_efficiency = 1.0
    if scenario.difficulty <= 2.0:
        phases_run = 4
        if paradigm_detected > 0.5:
            phases_run += 4
        elif gap_ratio >= params["gap_ratio_strong"]:
            phases_run += 3
        else:
            phases_run += 1

        max_phases = 12
        penalty = params["phase_skip_penalty"]
        scenario_efficiency = max(0.0, 1.0 - (phases_run / max_phases) * penalty * 3)
        scenario_efficiency += parallel_bonus  # parallel = more efficient

        if scenario.correct_action == "iterate" and passes_gate:
            scenario_efficiency *= (1.0 - penalty * 0.5 * (1.0 - self_check_reliability))

    elif scenario.difficulty >= 4.0:
        scenario_efficiency = min(1.0, assumption_coverage + 0.2 + (phase10_depth * 0.1))
        scenario_efficiency += parallel_bonus * 0.5

    scenario_efficiency = min(1.0, scenario_efficiency)

    # ── Baggage challenge rate ──
    baggage_challenge_rate = terminology_quality * params["baggage_presumption"]
    if agg_redesign:
        baggage_challenge_rate = min(1.0, baggage_challenge_rate * 1.15)

    # ── Phase 6: Confidence Scoring ──
    overall_reliability = min([assumption_coverage, bedrock_preservation, baggage_challenge_rate,
                                paradigm_detected if scenario.paradigm_exists else 1.0,
                                self_check_reliability])
    confidence_pass = overall_reliability >= params["confidence_min"]
    if not confidence_pass:
        action_correctness *= 0.8

    return FitnessScore(
        assumption_coverage=assumption_coverage,
        bedrock_preservation=bedrock_preservation,
        baggage_challenge_rate=baggage_challenge_rate,
        paradigm_detected=paradigm_detected,
        action_correctness=action_correctness,
        efficiency=scenario_efficiency,
    )


def evaluate_fitness(genome: List[float], scenarios: Optional[List[Scenario]] = None,
                     weights: Optional[dict] = None, seed: Optional[int] = None) -> Tuple[float, List[FitnessScore]]:
    if seed is not None:
        rng_state = random.getstate()
        random.seed(seed)

    scenarios = scenarios or SCENARIOS
    total = 0.0
    scores = []
    for scenario in scenarios:
        score = evaluate_genome_on_scenario(genome, scenario)
        score.compute_total(weights)
        scores.append(score)
        total += score.total

    avg = total / len(scenarios)

    if seed is not None:
        random.setstate(rng_state)

    return avg, scores


# ──────────────────────────────────────────────
# EVOLUTIONARY ALGORITHM — V2 MILLIONFOLD-STYLE
# ──────────────────────────────────────────────

@dataclass
class Individual:
    genome: List[float]
    fitness: float = 0.0
    scores: List[FitnessScore] = field(default_factory=list)
    params: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.params:
            self.params = decode(self.genome)


def tournament_select(population: List[Individual], tournament_size: int = 3) -> Individual:
    candidates = random.sample(population, tournament_size)
    return max(candidates, key=lambda ind: ind.fitness)


def crossover(a: List[float], b: List[float], rate: float = 0.5) -> Tuple[List[float], List[float]]:
    child_a = []
    child_b = []
    for ga, gb in zip(a, b):
        if random.random() < rate:
            child_a.append(gb)
            child_b.append(ga)
        else:
            child_a.append(ga)
            child_b.append(gb)
    return child_a, child_b


def mutate(genome: List[float], rate: float = 0.15, scale: float = 0.15) -> List[float]:
    """v2: higher default mutation rate for more exploration."""
    mutated = []
    for g in genome:
        if random.random() < rate:
            delta = random.gauss(0, scale)
            mutated.append(max(0.0, min(1.0, g + delta)))
        else:
            mutated.append(g)
    return mutated


def shock_mutate(genome: List[float], intensity: float = 0.5) -> List[float]:
    """v2: shock mutation — randomly reset a large fraction of genes."""
    mutated = []
    for g in genome:
        if random.random() < intensity:
            mutated.append(random.random())  # full random reset
        else:
            mutated.append(g)
    return mutated


def run_evolution(
    population_size: int = 80,
    generations: int = 30,
    tournament_size: int = 3,
    crossover_rate: float = 0.5,
    mutation_rate: float = 0.15,
    mutation_scale: float = 0.15,
    elitism: int = 2,
    diversity_preservation: float = 0.15,
    shock_every_n: int = 5,
    shock_intensity: float = 0.5,
    weights: Optional[dict] = None,
    scenarios: Optional[List[Scenario]] = None,
    seed: int = 42,
    verbose: bool = True,
    checkpoint_dir: str = "checkpoints_v2",
    load_from_v1: bool = False,
    v1_checkpoint_dir: str = "checkpoints",
) -> Tuple[Individual, List[Individual], List[dict]]:
    """
    v2 evolutionary loop with:
      - Higher population (80)
      - Higher mutation (0.15)
      - Diversity preservation (keep diverse individuals)
      - Shock mutations every N generations
      - Option to seed from v1 checkpoint
    """
    random.seed(seed)
    scenarios = scenarios or SCENARIOS
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Seed population
    population = []

    if load_from_v1:
        # Load v1 checkpoint and use it as seed population
        v1_final_path = os.path.join(v1_checkpoint_dir, "final.json")
        if os.path.exists(v1_final_path):
            print(f"  Loading v1 checkpoint from {v1_final_path}...")
            with open(v1_final_path) as f:
                v1_data = json.load(f)
            v1_best_genome = v1_data.get("best_genome", None)
            if v1_best_genome:
                # Extend v1 genome with structural gene defaults
                v2_genome = list(v1_best_genome) + [
                    encode({g.name: g.current for g in STRUCTURAL_GENES})[i]
                    for i in range(len(STRUCTURAL_GENES))
                ]
                # Ensure correct length
                while len(v2_genome) < GENOME_SIZE:
                    v2_genome.append(0.5)
                v2_genome = v2_genome[:GENOME_SIZE]

                ind = Individual(genome=v2_genome)
                fitness, scores = evaluate_fitness(ind.genome, scenarios, weights, seed=seed)
                ind.fitness = fitness
                ind.scores = scores
                population.append(ind)
                print(f"  Seeded v1 best (fitness: {fitness:.4f}) with structural gene defaults")
            else:
                print("  No best_genome in v1 checkpoint, starting fresh")
        else:
            print(f"  v1 checkpoint not found at {v1_final_path}, starting fresh")

    # If v1 load didn't produce individuals, seed with baseline
    if not population:
        baseline_genome = encode({g.name: g.current for g in ALL_GENES})
        ind = Individual(genome=baseline_genome[:])
        fitness, scores = evaluate_fitness(ind.genome, scenarios, weights, seed=seed)
        ind.fitness = fitness
        ind.scores = scores
        population.append(ind)

    # Fill rest of population with seeded variants
    while len(population) < population_size:
        base = random.choice(population[:max(1, len(population))])
        genome = base.genome[:]
        for j in range(GENOME_SIZE):
            r = random.random()
            if r < 0.5:
                genome[j] = max(0.0, min(1.0, genome[j] + random.gauss(0, 0.2)))
            elif r < 0.75:
                genome[j] = random.random()
            else:
                genome[j] = 0.0 if random.random() < 0.5 else 1.0
        ind = Individual(genome=genome)
        fitness, scores = evaluate_fitness(ind.genome, scenarios, weights, seed=seed + len(population))
        ind.fitness = fitness
        ind.scores = scores
        population.append(ind)

    population.sort(key=lambda ind: ind.fitness, reverse=True)

    history = []
    generation_best_fitness = []
    convergence_log = []

    for gen in range(generations):
        gen_start = time.time()

        # ── Shock mutation every N generations ──
        if shock_every_n > 0 and (gen + 1) % shock_every_n == 0:
            num_shocked = max(1, population_size // 5)
            for i in range(num_shocked):
                idx = population_size - 1 - i  # replace worst individuals
                if idx >= 0 and idx < len(population):
                    shocked = shock_mutate(population[idx].genome, shock_intensity)
                    ind = Individual(genome=shocked)
                    f, s = evaluate_fitness(ind.genome, scenarios, weights, seed=seed + gen * 1000 + i)
                    ind.fitness = f
                    ind.scores = s
                    population[idx] = ind
            if verbose:
                print(f"  ⚡ Shock mutation injected {num_shocked} individuals (gen {gen+1})")
            population.sort(key=lambda ind: ind.fitness, reverse=True)

        # ── Diversity preservation ──
        next_gen = population[:elitism]

        # Keep some diverse individuals (not just the fittest)
        if diversity_preservation > 0 and len(population) > elitism + 2:
            diverse_count = max(1, int(population_size * diversity_preservation))
            # Find individuals maximally distant from the current best
            best_genome = population[0].genome
            distances = [(i, genome_distance(best_genome, ind.genome))
                         for i, ind in enumerate(population[elitism:])]
            distances.sort(key=lambda x: x[1], reverse=True)
            for i in range(min(diverse_count, len(distances))):
                idx = distances[i][0] + elitism
                if idx < len(population) and population[idx] not in next_gen:
                    next_gen.append(population[idx])

        # Fill rest via tournament + crossover + mutation
        while len(next_gen) < population_size:
            p1 = tournament_select(population, tournament_size)
            p2 = tournament_select(population, tournament_size)
            c1, c2 = crossover(p1.genome, p2.genome, crossover_rate)
            c1 = mutate(c1, mutation_rate, mutation_scale)
            c2 = mutate(c2, mutation_rate, mutation_scale)

            ind1 = Individual(genome=c1)
            f1, s1 = evaluate_fitness(c1, scenarios, weights, seed=seed + gen * population_size + len(next_gen))
            ind1.fitness = f1
            ind1.scores = s1

            ind2 = Individual(genome=c2)
            f2, s2 = evaluate_fitness(c2, scenarios, weights, seed=seed + gen * population_size + len(next_gen) + 1)
            ind2.fitness = f2
            ind2.scores = s2

            next_gen.append(ind1)
            if len(next_gen) < population_size:
                next_gen.append(ind2)

        population = next_gen
        population.sort(key=lambda ind: ind.fitness, reverse=True)

        best = population[0]
        avg_fitness = sum(ind.fitness for ind in population) / len(population)
        diversity = sum(genome_distance(population[0].genome, ind.genome) for ind in population) / len(population)

        gen_time = time.time() - gen_start
        generation_best_fitness.append(best.fitness)

        record = {
            "generation": gen + 1,
            "best_fitness": round(best.fitness, 4),
            "avg_fitness": round(avg_fitness, 4),
            "diversity": round(diversity, 4),
            "improvement": round(best.fitness - (generation_best_fitness[-2] if len(generation_best_fitness) >= 2 else 0), 4),
            "time_s": round(gen_time, 2),
            "params": best.params,
            "scores_breakdown": [
                {
                    "scenario": s.name,
                    "assumption_coverage": round(score.assumption_coverage, 3),
                    "bedrock_preservation": round(score.bedrock_preservation, 3),
                    "baggage_challenge_rate": round(score.baggage_challenge_rate, 3),
                    "paradigm_detected": round(score.paradigm_detected, 3),
                    "action_correctness": round(score.action_correctness, 3),
                    "efficiency": round(score.efficiency, 3),
                    "total": round(score.total, 3),
                }
                for s, score in zip(scenarios, best.scores)
            ],
        }
        history.append(record)

        if verbose:
            delta = record["improvement"]
            arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
            print(f"Gen {gen+1:3d}/{generations} | best={best.fitness:.4f} | avg={avg_fitness:.4f} | "
                  f"div={diversity:.4f} | Δ={delta:+.4f} {arrow} | {gen_time:.1f}s")

        # Checkpoint every 10 generations
        if (gen + 1) % 10 == 0:
            checkpoint_file = os.path.join(checkpoint_dir, f"generation_{gen+1}.json")
            _save_checkpoint(checkpoint_file, best, population, gen, history)

    _save_checkpoint(
        os.path.join(checkpoint_dir, "final.json"),
        population[0], population, generations - 1, history
    )
    _export_csv(history, os.path.join(checkpoint_dir, "evolution.csv"))

    return population[0], population, history


def _save_checkpoint(path: str, best: Individual, population: List[Individual],
                     generation: int, history: List[dict]):
    """Save checkpoint to JSON."""
    data = {
        "generation": generation + 1,
        "best_fitness": best.fitness,
        "best_params": best.params,
        "best_genome": [round(g, 6) for g in best.genome],
        "scenario_scores": [
            {
                "scenario": s.name,
                "assumption_coverage": round(score.assumption_coverage, 3),
                "bedrock_preservation": round(score.bedrock_preservation, 3),
                "baggage_challenge_rate": round(score.baggage_challenge_rate, 3),
                "paradigm_detected": round(score.paradigm_detected, 3),
                "action_correctness": round(score.action_correctness, 3),
                "efficiency": round(score.efficiency, 3),
                "total": round(score.total, 3),
            }
            for s, score in zip(SCENARIOS, best.scores)
        ],
        "population_stats": {
            "size": len(population),
            "avg_fitness": round(sum(ind.fitness for ind in population) / len(population), 4),
            "max_fitness": round(max(ind.fitness for ind in population), 4),
            "min_fitness": round(min(ind.fitness for ind in population), 4),
            "std_fitness": round(
                math.sqrt(sum((ind.fitness - sum(ind.fitness for ind in population) / len(population)) ** 2
                              for ind in population) / len(population)),
                4
            ),
        },
        "gene_values": [
            {
                "name": g.name,
                "original": g.current,
                "optimal": best.params[g.name],
                "min": g.min_val,
                "max": g.max_val,
            }
            for g in ALL_GENES
        ],
        "history_length": len(history),
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _export_csv(history: List[dict], path: str):
    if not history:
        return
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["generation", "best_fitness", "avg_fitness", "diversity", "improvement", "time_s"])
        for h in history:
            writer.writerow([
                h["generation"], h["best_fitness"], h["avg_fitness"],
                h["diversity"], h["improvement"], h["time_s"],
            ])


# ──────────────────────────────────────────────
# ANALYSIS — V2 ENHANCED
# ──────────────────────────────────────────────

def analyze_results(checkpoint_dir: str = "checkpoints_v2", compare_v1: bool = True,
                    v1_dir: str = "checkpoints"):
    """Load v2 final checkpoint and print Millionfold-informed analysis."""
    final_path = os.path.join(checkpoint_dir, "final.json")
    if not os.path.exists(final_path):
        print(f"No checkpoint found at {final_path}")
        return

    with open(final_path) as f:
        data = json.load(f)

    # Load v1 for comparison
    v1_data = None
    v1_final_path = os.path.join(v1_dir, "final.json")
    if compare_v1 and os.path.exists(v1_final_path):
        with open(v1_final_path) as f:
            v1_data = json.load(f)

    print("=" * 80)
    print("  GEPA v2 — MILLIONFOLD-EVOLVED PROTOCOL OPTIMIZATION")
    print("=" * 80)

    print(f"\n  Generations completed: {data['history_length']}")
    print(f"  Best fitness:         {data['best_fitness']:.4f}")
    print(f"  Population avg:       {data['population_stats']['avg_fitness']:.4f}")
    print(f"  Population std:       {data['population_stats']['std_fitness']:.4f}")
    print(f"  Population diversity: {data['population_stats']['std_fitness']:.4f}")

    if v1_data:
        v1_best = v1_data['best_fitness']
        v2_best = data['best_fitness']
        delta = v2_best - v1_best
        print(f"\n  ── v1 → v2 Comparison ──")
        print(f"  v1 best: {v1_best:.4f}  →  v2 best: {v2_best:.4f}  (Δ = {delta:+.4f})")

    print("\n  ╔══════════════════════════════════════════════════════════════════════╗")
    print("  ║  PARAMETER OPTIMIZATION RESULTS (v2 — Millionfold-Enhanced)        ║")
    print("  ╠════════════════════╤══════════╤══════════╤══════════╤═══════════════╣")
    print("  ║ Parameter          │ Original │ Optimal  │ Delta    │ Shift         ║")
    print("  ╠════════════════════╪══════════╪══════════╪══════════╪═══════════════╣")

    # Separate v1 params from structural params
    v1_names = {g.name for g in GENE_DEFS_V1}
    structural_names = {g.name for g in STRUCTURAL_GENES}

    for gv in data["gene_values"]:
        orig = gv["original"]
        opt = gv["optimal"]
        delta = opt - orig
        pct = (delta / max(0.001, abs(orig))) * 100 if orig != 0 else float('inf')
        direction = "▲ increase" if delta > 0.01 else ("▼ decrease" if delta < -0.01 else "— unchanged")
        marker = "🧬" if gv["name"] in structural_names else "  "
        print(f"  ║ {marker} {gv['name']:22s} │ {orig:>8} │ {opt:>8} │ {delta:>+8.2f} │ {direction:10s} ║")

    print("  ╚════════════════════╧══════════╧══════════╧══════════╧═══════════════╝")

    if structural_names:
        print("  🧬 = Structural genes (new in v2 — evolved protocol structure)")

    print("\n  ╔══════════════════════════════════════════════════════════════════════╗")
    print("  ║  SCENARIO BREAKDOWN (best genome)                                  ║")
    print("  ╠════════════════════╤══════════╤══════════╤══════════╤══════════╤══════════╤══════════╣")
    print("  ║ Scenario           │ Assump.  │ Bedrock  │ Baggage  │ Paradigm │ Action   │ Effic.   ║")
    print("  ║                    │ Coverage │ Preserv. │ Challenge│ Detect   │ Correct  │          ║")
    print("  ╠════════════════════╪══════════╪══════════╪══════════╪══════════╪══════════╪══════════╣")

    for ss in data["scenario_scores"]:
        print(f"  ║ {ss['scenario']:18s} │ {ss['assumption_coverage']:>8.3f} │ "
              f"{ss['bedrock_preservation']:>8.3f} │ {ss['baggage_challenge_rate']:>8.3f} │ "
              f"{ss['paradigm_detected']:>8.3f} │ {ss['action_correctness']:>8.3f} │ "
              f"{ss['efficiency']:>8.3f} │")

    print("  ╚════════════════════╧══════════╧══════════╧══════════╧══════════╧══════════╧══════════╝")

    # ── Millionfold Insights ──
    print("\n  ═══  MILLIONFOLD-ENHANCED INSIGHTS  ═══\n")

    for gv in data["gene_values"]:
        orig = gv["original"]
        opt = gv["optimal"]
        delta_pct = ((opt - orig) / max(0.001, abs(orig))) * 100 if orig != 0 else float('inf')
        if abs(delta_pct) >= 10:
            is_structural = gv["name"] in structural_names
            tag = "🧬 STRUCTURAL" if is_structural else "📊 V1"
            if gv["name"] == "baggage_presumption":
                print(f"  [{tag}] {gv['name']}: {orig}→{opt} ({delta_pct:+.0f}%) — "
                      f"Protocol became {'more' if delta_pct > 0 else 'less'} aggressive at challenging claims.")
            elif gv["name"] == "gap_ratio_mandatory":
                print(f"  [{tag}] {gv['name']}: {orig}→{opt} ({delta_pct:+.0f}%) — "
                      f"Redesign threshold shifted. Higher = requires more evidence to force redesign.")
            elif gv["name"] == "gap_ratio_strong":
                print(f"  [{tag}] {gv['name']}: {orig}→{opt} ({delta_pct:+.0f}%) — "
                      f"Strong-indication threshold adjusted.")
            elif gv["name"] == "confidence_min":
                print(f"  [{tag}] {gv['name']}: {orig}→{opt} ({delta_pct:+.0f}%) — "
                      f"Confidence gate became {'stricter' if delta_pct > 0 else 'more lenient'}.")
            elif gv["name"] == "aggressive_redesign":
                val = "ENABLED" if opt > 0.5 else "disabled"
                print(f"  [{tag}] {gv['name']}: {val} — {'Defaulting to redesign.' if opt > 0.5 else 'Defaulting to iteration.'}")
            elif gv["name"] == "skip_importance_gate":
                val = "ENABLED" if opt > 0.5 else "disabled"
                print(f"  [{tag}] {gv['name']}: {val} — {'Skipping importance gate for simple tasks.' if opt > 0.5 else 'Running full gate always.'}")
            elif gv["name"] == "phase_parallel_pct":
                print(f"  [{tag}] {gv['name']}: {orig}→{opt:.2f} — "
                      f"{'More phases run in parallel.' if opt > 0.5 else 'Mostly sequential execution.'}")
            elif gv["name"] == "ceiling_ambition":
                print(f"  [{tag}] {gv['name']}: {orig}→{opt:.1f}x — "
                      f"Ceiling target magnitude set to 10^{opt:.0f}x improvement.")
            elif gv["name"] == "paradigm_aggression":
                print(f"  [{tag}] {gv['name']}: {orig}→{opt:.2f} — "
                      f"{'Relentless paradigm search.' if opt > 0.7 else 'Moderate search.'}")
            elif gv["name"] == "baggage_challenge_depth":
                print(f"  [{tag}] {gv['name']}: {orig}→{opt:.0f} — "
                      f"Drills {'deeper' if opt > orig else 'shallower'} into each claim.")
            elif gv["name"] == "fail_fast_on_ambiguity":
                print(f"  [{tag}] {gv['name']}: {orig}→{opt:.2f} — "
                      f"{'More aggressive at blocking vague requests.' if opt > 0.5 else 'More permissive.'}")
            else:
                print(f"  [{tag}] {gv['name']}: {orig}→{opt} ({delta_pct:+.0f}%)")

    # Baseline comparison
    print(f"\n  ── Baseline Comparison ──")
    baseline_genome = encode({g.name: g.current for g in ALL_GENES})
    baseline_fit, _ = evaluate_fitness(baseline_genome, weights=DEFAULT_WEIGHTS)
    print(f"  Original protocol (v2 genes at defaults): {baseline_fit:.4f}")
    print(f"  Optimized protocol (v2):                  {data['best_fitness']:.4f}")
    improvement = data['best_fitness'] - baseline_fit
    improvement_pct = (improvement / max(0.001, baseline_fit)) * 100
    print(f"  Improvement over baseline:                +{improvement:.4f} ({improvement_pct:+.1f}%)")

    if v1_data:
        v1_baseline = _calculate_v1_baseline()
        print(f"\n  v1 baseline (14 genes):                   {v1_baseline:.4f}")
        print(f"  v1 best:                                   {v1_data['best_fitness']:.4f}")
        v2_over_v1 = data['best_fitness'] - v1_data['best_fitness']
        print(f"  v2 improvement over v1 best:               +{v2_over_v1:.4f}")

    print(f"\n  ═══  RECOMMENDED PARAMETER SET (v2)  ═══\n")
    print("  ┌─────────────────────────────┬───────────┬───────────┐")
    print("  │ Parameter                   │ Value     │ Type      │")
    print("  ├─────────────────────────────┼───────────┼───────────┤")
    for gv in data["gene_values"]:
        gtype = "🧬 structural" if gv["name"] in structural_names else "📊 tuned"
        print(f"  │ {gv['name']:27s} │ {str(gv['optimal']):>9s} │ {gtype:9s} │")
    print("  └─────────────────────────────┴───────────┴───────────┘")

    return data


def _calculate_v1_baseline() -> float:
    """Calculate baseline fitness using v1 genes + structural defaults under MILLIONFOLD_WEIGHTS."""
    genome = []
    for g in GENE_DEFS_V1:
        norm = (g.current - g.min_val) / (g.max_val - g.min_val) if g.max_val != g.min_val else 0.5
        genome.append(norm)
    # Extend with structural gene defaults (v2 gene count)
    struct_defaults = encode({g.name: g.current for g in STRUCTURAL_GENES})
    full_genome = genome + struct_defaults
    fit, _ = evaluate_fitness(full_genome, weights=MILLIONFOLD_WEIGHTS)
    return fit


def load_real_scenarios(feedback_dir: str = "feedback") -> List[Scenario]:
    """
    Load real-world feedback-derived scenarios for inclusion in GEPA training.
    These replace (or supplement) the hand-authored SCENARIOS list,
    closing the loop: real outcomes → GEPA training → better parameters.
    """
    training_path = os.path.join(feedback_dir, "training_scenarios.json")
    if not os.path.exists(training_path):
        print(f"  ⚠ No training scenarios found at {training_path}")
        print(f"     Run feedback_harness.py --export-training-data first.")
        return []

    with open(training_path) as f:
        data = json.load(f)

    scenarios = []
    for sd in data.get("scenarios", []):
        s = Scenario(
            name=sd.get("name", "real_task"),
            description=sd.get("description", "Real-world feedback-derived scenario"),
            task_context=sd.get("task_context", ""),
            user_claims=sd.get("user_claims", []),
            hidden_assumptions=sd.get("hidden_assumptions", []),
            hidden_bedrocks=sd.get("hidden_bedrocks", []),
            hidden_baggage=sd.get("hidden_baggage", []),
            paradigm_exists=sd.get("paradigm_exists", False),
            correct_action=sd.get("correct_action", "iterate"),
            difficulty=sd.get("difficulty", 1.0),
        )
        scenarios.append(s)

    return scenarios


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GEPA v2 — Millionfold-Evolved Protocol Optimizer")
    parser.add_argument("--generations", type=int, default=30, help="Number of generations")
    parser.add_argument("--population", type=int, default=80, help="Population size")
    parser.add_argument("--seed", type=int, default=137, help="Random seed (new seed for v2)")
    parser.add_argument("--mutation-rate", type=float, default=0.15, help="Mutation rate")
    parser.add_argument("--mutation-scale", type=float, default=0.15, help="Mutation scale")
    parser.add_argument("--shock-every", type=int, default=5, help="Shock mutation interval (0=off)")
    parser.add_argument("--diversity-pct", type=float, default=0.15, help="Diversity preservation fraction")
    parser.add_argument("--quick", action="store_true", help="Quick run: 10 gens, pop 30")
    parser.add_argument("--analyze-only", action="store_true", help="Analyze last run without evolving")
    parser.add_argument("--resume-from-v1", action="store_true", default=True,
                        help="Seed population from v1 checkpoint (default: True)")
    parser.add_argument("--checkpoint-dir", default="checkpoints_v2", help="Checkpoint directory")
    parser.add_argument("--v1-dir", default="checkpoints", help="v1 checkpoint directory")
    parser.add_argument("--verbose", action="store_true", default=True)
    parser.add_argument("--with-real-scenarios", action="store_true", default=False,
                        help="Include feedback-derived real-world scenarios in training")
    parser.add_argument("--feedback-dir", default="feedback",
                        help="Directory containing feedback training data")

    args = parser.parse_args()

    if args.quick:
        args.generations = 10
        args.population = 30

    if args.analyze_only:
        sys.exit(analyze_results(args.checkpoint_dir, compare_v1=True, v1_dir=args.v1_dir))

    # ── Load real-world scenarios ──
    merged_scenarios = list(SCENARIOS)
    if args.with_real_scenarios:
        real_scenarios = load_real_scenarios(args.feedback_dir)
        if real_scenarios:
            merged_scenarios.extend(real_scenarios)
            print(f"  ✅ Loaded {len(real_scenarios)} real-world scenarios from feedback/")

    print(f"\n  ╔══════════════════════════════════════════════════════════════════════╗")
    print(f"  ║  GEPA v2 — Millionfold-Evolved Protocol Optimization               ║")
    print(f"  ║  Applying Millionfold's OWN protocol to the optimization process    ║")
    print(f"  ╟──────────────────────────────────────────────────────────────────────╢")
    print(f"  ║  Generations:   {args.generations:3d}  │ Population: {args.population:3d}                    ║")
    print(f"  ║  Mutation rate: {args.mutation_rate:.2f}  │ Scale: {args.mutation_scale:.2f}  │ Shock: every {args.shock_every} gen  ║")
    print(f"  ║  Genome size:   {GENOME_SIZE:3d} genes ({len(GENE_DEFS_V1)} tuned + {len(STRUCTURAL_GENES)} structural)    ║")
    real_label = f" ({len(merged_scenarios)-len(SCENARIOS)} real)" if len(merged_scenarios) > len(SCENARIOS) else ""
    print(f"  ║  Scenarios:     {len(merged_scenarios):3d}{real_label}  │ Diversity preservation: {args.diversity_pct:.0%}         ║")
    print(f"  ║  Seed from v1:  {args.resume_from_v1}                                    ║")
    print(f"  ╚══════════════════════════════════════════════════════════════════════╝\n")

    start = time.time()
    best, population, history = run_evolution(
        population_size=args.population,
        generations=args.generations,
        mutation_rate=args.mutation_rate,
        mutation_scale=args.mutation_scale,
        shock_every_n=args.shock_every,
        diversity_preservation=args.diversity_pct,
        seed=args.seed,
        verbose=args.verbose,
        checkpoint_dir=args.checkpoint_dir,
        load_from_v1=args.resume_from_v1,
        v1_checkpoint_dir=args.v1_dir,
        scenarios=merged_scenarios,
    )
    elapsed = time.time() - start

    print(f"\n  ✅ v2 evolution complete in {elapsed:.1f}s")
    print(f"     Best fitness: {best.fitness:.4f}")
    print(f"     Best params: {best.params}\n")

    analyze_results(args.checkpoint_dir, compare_v1=True, v1_dir=args.v1_dir)


if __name__ == "__main__":
    main()
