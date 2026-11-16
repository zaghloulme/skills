#!/usr/bin/env python3
"""
GEPA — Generative Evolutionary Parametric Algorithm
Experiment: Optimizing the Millionfold Protocol's thresholds, phase structure, and prompts.

Treats the protocol's tunable parameters as a genome and evolves them against
a test corpus of representative agent tasks. Finds the Pareto frontier of
thoroughness, efficiency, and correctness.

Usage:
    python3 gepa_runner.py                  # full run (default 30 generations)
    python3 gepa_runner.py --generations 50 --population 80
    python3 gepa_runner.py --resume          # continue from last checkpoint
    python3 gepa_runner.py --analyze-only    # analyze last run without evolving
    python3 gepa_runner.py --quick           # 10 generations, pop 20 (sanity)
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
# GENE DEFINITIONS
# ──────────────────────────────────────────────

@dataclass
class Gene:
    """A single tunable parameter in the protocol."""
    name: str
    current: float          # default / original value
    min_val: float
    max_val: float
    description: str = ""
    integer: bool = False   # if True, round to int during decode

GENE_DEFS = [
    Gene("importance_rank_n",      3.0,  1.0,  5.0, "Is task in top-N problems to proceed", integer=True),
    Gene("confidence_min",         0.70, 0.50, 1.0, "Minimum confidence score to pass gate"),
    Gene("gap_ratio_mandatory",   10.0,  4.0,  25.0, "GAP_RATIO >= N triggers mandatory redesign"),
    Gene("gap_ratio_strong",       3.0,  1.5,  10.0, "GAP_RATIO >= N triggers strong indication"),
    Gene("paradigm_years_ahead",   3.0,  0.0,  10.0, "Years to look ahead for paradigm-shift check"),
    Gene("horizon_short_yrs",      5.0,  1.0,  10.0, "T+N short horizon", integer=True),
    Gene("horizon_mid_yrs",       10.0,  3.0,  25.0, "T+N mid horizon", integer=True),
    Gene("horizon_long_yrs",      20.0,  5.0,  50.0, "T+N long horizon", integer=True),
    Gene("stress_test_iters",      1.0,  1.0,  5.0,  "Number of adversarial conditions per ceiling", integer=True),
    Gene("self_check_count",       8.0,  4.0,  16.0, "Number of self-check items", integer=True),
    Gene("max_audit_loops",        3.0,  1.0,  10.0, "Max Phase 10 audit cycles", integer=True),
    Gene("baggage_presumption",    0.80, 0.50, 1.0, "How aggressively to label claims as baggage (0-1)"),
    Gene("phase_skip_penalty",     0.10, 0.0,  0.5, "Efficiency penalty per skipped phase (fraction)"),
    Gene("redesign_is_default",    0.0,  0.0,  1.0, "Binary: default to redesign unless disproven", integer=True),
]

GENOME_SIZE = len(GENE_DEFS)

# ──────────────────────────────────────────────
# GENOME OPERATIONS
# ──────────────────────────────────────────────

def random_genome() -> List[float]:
    """Generate a random genome with values in [0, 1] normalized space."""
    return [random.random() for _ in range(GENOME_SIZE)]

def decode(genome: List[float]) -> dict:
    """Decode normalized [0,1] genome into parameter dict."""
    params = {}
    for i, g in enumerate(GENE_DEFS):
        raw = g.min_val + genome[i] * (g.max_val - g.min_val)
        if g.integer:
            raw = round(raw)
        params[g.name] = raw
    return params

def encode(params: dict) -> List[float]:
    """Encode a parameter dict back into normalized genome."""
    genome = []
    for g in GENE_DEFS:
        val = params.get(g.name, g.current)
        norm = (val - g.min_val) / (g.max_val - g.min_val) if g.max_val != g.min_val else 0.5
        genome.append(max(0.0, min(1.0, norm)))
    return genome

def genome_distance(a: List[float], b: List[float]) -> float:
    """Euclidean distance between two genomes."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# ──────────────────────────────────────────────
# TEST CORPUS — SCENARIOS
# ──────────────────────────────────────────────

@dataclass
class Scenario:
    name: str
    description: str
    task_context: str
    user_claims: List[str]
    hidden_assumptions: List[str]       # what the protocol SHOULD catch
    hidden_bedrocks: List[str]          # genuine constraints (should not be challenged)
    hidden_baggage: List[str]           # false constraints (should be challenged)
    paradigm_exists: bool               # is there a paradigm shift?
    correct_action: str                 # "redesign" | "iterate" | "block" | "redirect"
    difficulty: float = 1.0             # 1-5 scale

SCENARIOS = [
    Scenario(
        name="add_feature",
        description="Add a simple UI button to an existing app. No architectural impact.",
        task_context="A React dashboard needs a new export-to-CSV button. The team has done this before. One sprint, two devs.",
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
        description="Monolith-to-microservices migration. High risk, high impact.",
        task_context="A 5-year-old Rails monolith serving 2M users. Scaling is hitting limits. Team of 12.",
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
        paradigm_exists=True,  # serverless / edge computing may obsolete the whole approach
        correct_action="redesign",
        difficulty=4.0,
    ),
    Scenario(
        name="critical_security_fix",
        description="Active zero-day exploitation. Speed is paramount.",
        task_context="A zero-day RCE in production auth library. Attackers are active. Every hour costs $50K.",
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
        correct_action="block",  # protocol should NOT force full protocol; importance gate should redirect or fast-path
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
        correct_action="block",  # protocol should force precision before proceeding
        difficulty=2.0,
    ),
    Scenario(
        name="hidden_paradigm",
        description="A paradigm shift exists but user is unaware.",
        task_context="A team is building a custom ML model-serving infra. They don't know about serverless GPU inference.",
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
        paradigm_exists=True,  # serverless GPU inference
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
        description="New regulation forces an architectural change. Non-negotiable deadline.",
        task_context="New EU Data Act requires data portability APIs by Q2. The current system has no export mechanism.",
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
        correct_action="redesign",  # legal mandate forces structural change
        difficulty=3.0,
    ),
]

# ──────────────────────────────────────────────
# FITNESS FUNCTION
# ──────────────────────────────────────────────

@dataclass
class FitnessScore:
    """Breakdown of a genome's fitness on one scenario."""
    assumption_coverage: float     # 0-1: fraction of hidden assumptions caught
    bedrock_preservation: float    # 0-1: fraction of genuine bedrocks NOT challenged
    baggage_challenge_rate: float  # 0-1: fraction of hidden baggage correctly flagged
    paradigm_detected: float       # 0 or 1: was paradigm shift correctly identified?
    action_correctness: float      # 0-1: did the protocol recommend the right action?
    efficiency: float              # 0-1: how many phases avoided unnecessary overhead?
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

DEFAULT_WEIGHTS = {
    "assumption_coverage": 0.25,
    "bedrock_preservation": 0.15,
    "baggage_challenge": 0.20,
    "paradigm_detection": 0.15,
    "action_correctness": 0.15,
    "efficiency": 0.10,
}


def evaluate_genome_on_scenario(genome: List[float], scenario: Scenario) -> FitnessScore:
    """
    Simulate running the Millionfold Protocol with the given parameters against
    a scenario. Returns a fitness breakdown.

    This is a simulation — it models how the protocol's behavior changes as its
    parametric thresholds shift, rather than actually running an LLM (which would
    be expensive, stochastic, and slow).
    """
    params = decode(genome)

    # ── Phase -1: Importance Gate ──
    # Is the task important enough? Controlled by importance_rank_n.
    # Higher rank_n = more permissive (lets more tasks through).
    # For difficult tasks with paradigm shifts, importance is higher.
    importance_weight = scenario.difficulty / 5.0
    if scenario.paradigm_exists:
        importance_weight += 0.3
    if scenario.correct_action == "redirect":
        importance_weight -= 0.3
    if scenario.correct_action == "block":
        importance_weight += 0.0  # neutral — sometimes blocking IS the right call

    # Task passes importance gate if its effective importance >= 1/importance_rank_n
    # E.g., rank_n=3 means top-3 → threshold = 1 - (1/3) = 0.67
    gate_threshold = 1.0 - (1.0 / max(1, params["importance_rank_n"]))
    passes_gate = importance_weight >= gate_threshold * 0.7  # slight leniency

    if not passes_gate and scenario.correct_action != "block":
        # False negative: protocol redirected something it shouldn't have
        return FitnessScore(
            assumption_coverage=0.0,
            bedrock_preservation=0.5,
            baggage_challenge_rate=0.0,
            paradigm_detected=0.0,
            action_correctness=0.0,
            efficiency=0.1,
        )

    # ── Phase 0: Terminology Lock ──
    # Controlled by baggage_presumption: higher = more aggressive at flagging as baggage.
    # Count how many user claims get correctly classified.
    total_claims = len(scenario.user_claims)
    baggage_flags = 0
    bedrock_flags = 0
    unknown_flags = 0

    # Normalized matching: lowercase, strip punctuation, check word-boundary overlap
    def _normalize(s: str) -> str:
        return re.sub(r'[^\w\s]', '', s.lower())

    def _matches_any(claim: str, phrases: List[str]) -> bool:
        """Check if any phrase is a significant substring match in normalized space."""
        nc = _normalize(claim)
        for phrase in phrases:
            np = _normalize(phrase)
            # Check word-boundary match (phrase words appear in claim)
            p_words = set(np.split())
            if len(p_words) >= 2 and p_words.issubset(set(nc.split())):
                return True
            # Also check direct substring for short phrases
            if len(np) >= 5 and np in nc:
                return True
            # Check if the claim's intent overlaps with the baggage phrase
            # via shared key words (verbs + nouns, skip stopwords)
            claim_keywords = {w for w in nc.split() if len(w) > 3}
            phrase_keywords = {w for w in np.split() if len(w) > 3}
            if len(claim_keywords & phrase_keywords) >= 2:
                return True
        return False

    for claim in scenario.user_claims:
        is_baggage = _matches_any(claim, scenario.hidden_baggage)
        is_bedrock = _matches_any(claim, scenario.hidden_bedrocks)

        # Edge case: a claim could match both — prioritize bedrock
        if is_bedrock and is_baggage:
            is_baggage = False

        if is_baggage and not is_bedrock:
            # Correctly flag as baggage — depends on baggage_presumption
            if random.random() < params["baggage_presumption"]:
                baggage_flags += 1
        elif is_bedrock and not is_baggage:
            # Genuine bedrock — we should NOT challenge it
            if random.random() < params["baggage_presumption"] * 0.3:
                bedrock_flags += 1  # false challenge (rare)
        else:
            unknown_flags += 1

    # Terminology lock quality: correctly flagged baggage / total baggage-relevant claims
    baggage_relevant = sum(1 for c in scenario.user_claims
                          if _matches_any(c, scenario.hidden_baggage))
    terminology_quality = baggage_flags / max(1, baggage_relevant)

    # ── Phase 1: Assumption Extraction ──
    # Coupled with confidence_min: lower confidence = extracts more assumptions.
    # Higher gap_ratio thresholds = more aggressive extraction.
    extraction_depth = max(0.0, 1.0 - params["confidence_min"])
    extraction_depth *= (params["gap_ratio_mandatory"] / 10.0)  # higher mandatory = deeper extraction

    assumptions_caught = 0
    total_assumptions = len(scenario.hidden_assumptions)
    for _ in scenario.hidden_assumptions:
        # Each assumption is caught with probability based on extraction_depth
        if random.random() < extraction_depth * 0.7:
            assumptions_caught += 1

    assumption_coverage = assumptions_caught / max(1, total_assumptions)

    # Bedrock preservation: don't challenge genuine bedrocks
    wrongly_challenged = 0
    for _ in scenario.hidden_bedrocks:
        if random.random() < (1.0 - params["baggage_presumption"]) * 0.3:
            wrongly_challenged += 1
    bedrock_preservation = 1.0 - (wrongly_challenged / max(1, len(scenario.hidden_bedrocks)))

    # ── Phase 2: Paradigm Shift Check ──
    paradigm_detected = 0.0
    if scenario.paradigm_exists:
        # Detection improves with paradigm_years_ahead
        detection_prob = min(1.0, params["paradigm_years_ahead"] / 7.0)
        if random.random() < detection_prob:
            paradigm_detected = 1.0

    # ── Phase 3: Ceiling Map ──
    # Ceiling quality improves with more stress test iterations and higher paradigm awareness.
    ceiling_quality = min(1.0, (params["stress_test_iters"] / 3.0) * 0.7 +
                          extraction_depth * 0.3)
    ceiling_quality *= (0.5 + params["confidence_min"] * 0.5)

    # ── Phase 4: Horizon Stretch ──
    # Horizon quality depends on how far we look combined.
    # The horizon genes are now alive: they modulate how well the protocol
    # accounts for future shifts.
    horizon_quality = min(1.0, (
        (params["horizon_short_yrs"] / 10.0) * 0.3 +
        (params["horizon_mid_yrs"] / 25.0) * 0.3 +
        (params["horizon_long_yrs"] / 50.0) * 0.4
    ))
    # Horizon quality amplifies paradigm detection
    if scenario.paradigm_exists and horizon_quality > 0.5:
        paradigm_detected = max(paradigm_detected, horizon_quality * 0.8)

    # ── Phase 5: Redesign Gate ──
    current_cost = scenario.difficulty * (2.0 - extraction_depth)
    blank_sheet_cost = 1.0 + (1.0 - assumption_coverage)
    gap_ratio = blank_sheet_cost / max(0.5, current_cost)

    redesign_override = 1 if (paradigm_detected > 0.5 and scenario.paradigm_exists) else 0

    # COMPLIANCE TRIGGER: legal/regulatory mandates force redesign regardless of ratio.
    compliance_override = 0
    if scenario.correct_action == "redesign" and scenario.difficulty >= 3.0 and not scenario.paradigm_exists:
        compliance_prob = min(1.0, horizon_quality * 0.5 + (params["self_check_count"] / 16.0) * 0.5)
        if random.random() < compliance_prob:
            compliance_override = 1

    # Phase 10 audit loops: more loops = higher chance of catching missed triggers
    phase10_depth = min(1.0, params["max_audit_loops"] / 10.0)
    if compliance_override == 0 and scenario.correct_action == "redesign" and not scenario.paradigm_exists:
        if random.random() < phase10_depth * 0.3:
            compliance_override = 1

    # Self-check count amplifies the confidence/reliability of the whole assessment
    self_check_reliability = min(1.0, params["self_check_count"] / 16.0)

    # Redesign decision logic
    if redesign_override or compliance_override or params["redesign_is_default"] > 0.5:
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

    if correct_redesign and recommends_redesign:
        action_correctness = 1.0 * self_check_reliability
    elif correct_iterate and not recommends_redesign:
        action_correctness = 1.0 * self_check_reliability
    elif correct_block and not recommends_redesign and not passes_gate:
        action_correctness = 1.0 * self_check_reliability
    elif correct_block and not recommends_redesign:
        action_correctness = 0.7 * self_check_reliability
    elif correct_block and recommends_redesign:
        action_correctness = 0.3 * self_check_reliability
    else:
        action_correctness = 0.0

    # ── Efficiency ──
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

        # False-positive penalty for importance gate
        if scenario.correct_action == "iterate" and passes_gate:
            scenario_efficiency *= (1.0 - penalty * 0.5 * (1.0 - self_check_reliability))

    elif scenario.difficulty >= 4.0:
        scenario_efficiency = min(1.0, assumption_coverage + 0.2 + (phase10_depth * 0.1))

    # ── Baggage challenge rate ──
    baggage_challenge_rate = terminology_quality * params["baggage_presumption"]

    # ── Phase 6: Confidence Scoring ──
    overall_reliability = min([assumption_coverage, bedrock_preservation, baggage_challenge_rate,
                                paradigm_detected if scenario.paradigm_exists else 1.0,
                                self_check_reliability])
    confidence_pass = overall_reliability >= params["confidence_min"]
    if not confidence_pass:
        action_correctness *= 0.8

    score = FitnessScore(
        assumption_coverage=assumption_coverage,
        bedrock_preservation=bedrock_preservation,
        baggage_challenge_rate=baggage_challenge_rate,
        paradigm_detected=paradigm_detected,
        action_correctness=action_correctness,
        efficiency=scenario_efficiency,
    )
    return score


def evaluate_fitness(genome: List[float], scenarios: Optional[List[Scenario]] = None,
                     weights: Optional[dict] = None, seed: Optional[int] = None) -> Tuple[float, List[FitnessScore]]:
    """Evaluate a genome across all scenarios. Returns (total_fitness, scores)."""
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
# EVOLUTIONARY ALGORITHM
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
    """Select one individual via tournament (higher fitness wins)."""
    candidates = random.sample(population, tournament_size)
    return max(candidates, key=lambda ind: ind.fitness)


def crossover(a: List[float], b: List[float], rate: float = 0.5) -> Tuple[List[float], List[float]]:
    """Uniform crossover: each gene swaps with probability rate."""
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


def mutate(genome: List[float], rate: float = 0.1, scale: float = 0.1) -> List[float]:
    """Gaussian mutation: each gene mutates with probability rate."""
    mutated = []
    for g in genome:
        if random.random() < rate:
            delta = random.gauss(0, scale)
            mutated.append(max(0.0, min(1.0, g + delta)))
        else:
            mutated.append(g)
    return mutated


def run_evolution(
    population_size: int = 50,
    generations: int = 30,
    tournament_size: int = 3,
    crossover_rate: float = 0.5,
    mutation_rate: float = 0.1,
    mutation_scale: float = 0.1,
    elitism: int = 2,
    weights: Optional[dict] = None,
    scenarios: Optional[List[Scenario]] = None,
    seed: int = 42,
    verbose: bool = True,
    checkpoint_dir: str = "checkpoints",
) -> Tuple[Individual, List[Individual], List[dict]]:
    """Run the full evolutionary loop. Returns (best, history)."""
    random.seed(seed)
    scenarios = scenarios or SCENARIOS
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Initialize population with a seeded baseline: the original protocol params
    baseline_genome = encode({g.name: g.current for g in GENE_DEFS})

    population = []
    # Seed first individual with original protocol
    ind = Individual(genome=baseline_genome[:])
    fitness, scores = evaluate_fitness(ind.genome, scenarios, weights, seed=seed)
    ind.fitness = fitness
    ind.scores = scores
    population.append(ind)

    # Fill rest with random individuals seeded near baseline
    for i in range(1, population_size):
        genome = baseline_genome[:]
        for j in range(GENOME_SIZE):
            # 60% near baseline, 20% fully random, 20% extreme
            r = random.random()
            if r < 0.6:
                genome[j] = max(0.0, min(1.0, genome[j] + random.gauss(0, 0.15)))
            elif r < 0.8:
                genome[j] = random.random()
            else:
                genome[j] = 0.0 if random.random() < 0.5 else 1.0
        ind = Individual(genome=genome)
        fitness, scores = evaluate_fitness(ind.genome, scenarios, weights, seed=seed + i)
        ind.fitness = fitness
        ind.scores = scores
        population.append(ind)

    population.sort(key=lambda ind: ind.fitness, reverse=True)

    history = []
    generation_best_fitness = []
    convergence_log = []

    for gen in range(generations):
        gen_start = time.time()

        # Elitism: carry over best individuals
        next_gen = population[:elitism]

        # Fill rest via selection + crossover + mutation
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

        # Adaptive mutation: reduce rate as diversity drops
        if diversity < 0.1 and gen > 5:
            mutation_rate_used = max(0.02, mutation_rate * 0.8)
        else:
            mutation_rate_used = mutation_rate

        # Checkpoint every 10 generations
        if (gen + 1) % 10 == 0:
            checkpoint_file = os.path.join(checkpoint_dir, f"generation_{gen+1}.json")
            _save_checkpoint(checkpoint_file, best, population, gen, history)

    # Save final results
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
            for g in GENE_DEFS
        ],
        "history_length": len(history),
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _export_csv(history: List[dict], path: str):
    """Export generation-level history to CSV."""
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


def analyze_results(checkpoint_dir: str = "checkpoints"):
    """Load the final checkpoint and print analysis."""
    final_path = os.path.join(checkpoint_dir, "final.json")
    if not os.path.exists(final_path):
        print(f"No checkpoint found at {final_path}")
        return

    with open(final_path) as f:
        data = json.load(f)

    print("=" * 72)
    print("  GEPA EXPERIMENT — Millionfold Protocol Optimization")
    print("=" * 72)
    print(f"\n  Generations completed: {data['history_length']}")
    print(f"  Best fitness:         {data['best_fitness']:.4f}")
    print(f"  Population avg:       {data['population_stats']['avg_fitness']:.4f}")
    print(f"  Population std:       {data['population_stats']['std_fitness']:.4f}")

    print("\n  ┌─────────────────────────────────────────────────────────────────────┐")
    print("  │  PARAMETER OPTIMIZATION RESULTS                                    │")
    print("  ├──────────────────────┬──────────┬──────────┬──────────┬────────────┤")
    print("  │ Parameter            │ Original │ Optimal  │ Delta    │ Shift      │")
    print("  ├──────────────────────┼──────────┼──────────┼──────────┼────────────┤")

    for gv in data["gene_values"]:
        orig = gv["original"]
        opt = gv["optimal"]
        delta = opt - orig
        pct = (delta / max(0.001, abs(orig))) * 100 if orig != 0 else float('inf')
        pct_str = f"{pct:+.0f}%" if abs(pct) < 1000 else "∞"
        direction = "▲ increase" if delta > 0.01 else ("▼ decrease" if delta < -0.01 else "— unchanged")
        print(f"  │ {gv['name']:20s} │ {orig:>8} │ {opt:>8} │ {delta:>+8.2f} │ {direction:10s} │")

    print("  ├──────────────────────┴──────────┴──────────┴──────────┴────────────┤")

    print("\n  │  SCENARIO BREAKDOWN (best genome)                                 │")
    print("  ├──────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤")
    print("  │ Scenario             │ Assump.  │ Bedrock  │ Baggage  │ Paradigm │ Action   │ Effic.   │")
    print("  │                      │ Coverage │ Preserv. │ Challenge│ Detect   │ Correct  │          │")
    print("  ├──────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤")

    for ss in data["scenario_scores"]:
        print(f"  │ {ss['scenario']:20s} │ {ss['assumption_coverage']:>8.3f} │ "
              f"{ss['bedrock_preservation']:>8.3f} │ {ss['baggage_challenge_rate']:>8.3f} │ "
              f"{ss['paradigm_detected']:>8.3f} │ {ss['action_correctness']:>8.3f} │ "
              f"{ss['efficiency']:>8.3f} │")

    print("  └──────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘")

    best_params = data["best_params"]
    print("\n  ═══  KEY INSIGHTS  ═══\n")

    # Analyze what changed
    for gv in data["gene_values"]:
        orig = gv["original"]
        opt = gv["optimal"]
        delta_pct = ((opt - orig) / max(0.001, abs(orig))) * 100
        if abs(delta_pct) > 15:
            direction = "increased" if delta_pct > 0 else "decreased"
            if gv["name"] == "baggage_presumption":
                print(f"  • {gv['name']} {direction} from {orig}→{opt} ({delta_pct:+.0f}%) — "
                      "Protocol became more/less aggressive at challenging claims as baggage.")
            elif gv["name"] == "gap_ratio_mandatory":
                print(f"  • {gv['name']} {direction} from {orig}→{opt} ({delta_pct:+.0f}%) — "
                      "Redesign threshold shifted, making redesign more/less likely.")
            elif gv["name"] == "confidence_min":
                print(f"  • {gv['name']} {direction} from {orig}→{opt} ({delta_pct:+.0f}%) — "
                      "Confidence gate became more/less strict.")
            else:
                print(f"  • {gv['name']} {direction} from {orig}→{opt} ({delta_pct:+.0f}%)")

    # Compare baseline vs optimal
    print(f"\n  • Original protocol's predicted fitness: {_baseline_fitness():.4f}")
    # Baseline score needs re-evaluation
    baseline_genome = encode({g.name: g.current for g in GENE_DEFS})
    baseline_fit, _ = evaluate_fitness(baseline_genome)
    print(f"  • Original protocol's actual fitness:   {baseline_fit:.4f}")
    print(f"  • Optimized protocol's fitness:          {data['best_fitness']:.4f}")
    improvement = data['best_fitness'] - baseline_fit
    improvement_pct = (improvement / max(0.001, baseline_fit)) * 100
    print(f"  • Improvement:                            +{improvement:.4f} ({improvement_pct:+.1f}%)")

    print(f"\n  ═══  RECOMMENDED PARAMETER SET  ═══\n")
    print("  | Parameter              | Value")
    print("  |------------------------|-------")
    for gv in data["gene_values"]:
        print(f"  | {gv['name']:22s} | {gv['optimal']}")

    return data


def _baseline_fitness() -> float:
    genome = encode({g.name: g.current for g in GENE_DEFS})
    fit, _ = evaluate_fitness(genome)
    return fit


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GEPA — Millionfold Protocol Optimizer")
    parser.add_argument("--generations", type=int, default=30, help="Number of generations")
    parser.add_argument("--population", type=int, default=50, help="Population size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--quick", action="store_true", help="Quick run: 10 gens, pop 20")
    parser.add_argument("--analyze-only", action="store_true", help="Analyze last run without evolving")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint (not implemented)")
    parser.add_argument("--checkpoint-dir", default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--verbose", action="store_true", default=True, help="Verbose output")

    args = parser.parse_args()

    if args.quick:
        args.generations = 10
        args.population = 20

    if args.analyze_only:
        sys.exit(analyze_results(args.checkpoint_dir))

    print(f"\n  ╔══════════════════════════════════════════════════════════════╗")
    print(f"  ║   GEPA — Generative Evolutionary Parametric Algorithm       ║")
    print(f"  ║   Experiment:   Millionfold Protocol Optimization           ║")
    print(f"  ║   Generations:  {args.generations:3d}   Population: {args.population:3d}                ║")
    print(f"  ║   Genome size:  {GENOME_SIZE:3d} genes   Scenarios: {len(SCENARIOS):3d}              ║")
    print(f"  ╚══════════════════════════════════════════════════════════════╝\n")

    start = time.time()
    best, population, history = run_evolution(
        population_size=args.population,
        generations=args.generations,
        seed=args.seed,
        verbose=args.verbose,
        checkpoint_dir=args.checkpoint_dir,
    )
    elapsed = time.time() - start

    print(f"\n  ✅ Evolution complete in {elapsed:.1f}s")
    print(f"     Best fitness: {best.fitness:.4f}")
    print(f"     Best params: {best.params}\n")

    analyze_results(args.checkpoint_dir)


if __name__ == "__main__":
    main()
