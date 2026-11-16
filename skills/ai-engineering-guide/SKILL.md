---
name: ai-engineering-guide
description: >
  Guidelines for building AI agents, AI apps, and LLM-powered systems. Covers agent architecture
  (ReAct, plan-execute, multi-agent, workflow), prompt engineering (few-shot, chain-of-thought,
  structured output), RAG and grounding (chunking, retrieval, re-ranking), security hardening
  (OWASP LLM Top 10, prompt injection defense), evaluation (LLM-as-judge, RAGAS, groundedness),
  model selection, orchestration patterns, and AI product lifecycle. Use when asked to design AI
  agents, build AI apps, implement prompts, set up RAG, evaluate LLM outputs, secure AI systems,
  select models, or plan AI product lifecycles. Triggers: "build an AI agent", "design a prompt",
  "set up RAG", "evaluate my LLM", "AI architecture", "orchestration workflow", "prompt template",
  "reduce hallucinations", "LLM testing", "agent tools", "multi-agent system".
metadata:
  author: AI Engineering Practice
  version: 2.0.0
  category: ai-development
  tags: [ai-agents, prompt-engineering, rag, llm, evaluation, security, orchestration, lifecycle]
---

# AI Engineering Guide

A generalized, platform-agnostic guide for building AI agents, AI applications, and LLM-powered systems. Distilled from enterprise AI training curricula and industry best practices.

## How to Use This Skill

This skill follows progressive disclosure:
- **This file** contains concise summaries of all 8 knowledge areas -- enough to guide most decisions.
- **`references/` files** contain deep guidance for each area -- consult when you need specifics.

**Quick Reference: Which file to consult?**

| Question | Reference File |
|----------|---------------|
| How do I write better prompts? | `references/prompt-engineering.md` |
| How do I reduce hallucinations with RAG? | `references/rag-and-grounding.md` |
| How do I design an AI agent? | `references/agent-design.md` |
| How do I protect against prompt injection? | `references/security-and-hardening.md` |
| How do I test LLM outputs? | `references/evaluation-and-testing.md` |
| Which model should I use? | `references/model-selection.md` |
| How do I build a production AI pipeline? | `references/orchestration-patterns.md` |
| How do I plan and ship an AI product? | `references/ai-product-lifecycle.md` |

---

## 1. AI Agent Design & Architecture

Agentic AI represents systems that can reason, plan, and autonomously complete complex multi-step tasks. Effective agent design requires clear boundaries between autonomy and human oversight.

**Core Principles:**
- **Decomposition**: Break complex tasks into discrete, verifiable steps
- **Tool Design**: Define minimum toolset with clear descriptions, typed parameters, and informative errors. 5 well-designed tools outperform 50 poorly-scoped ones.
- **Human-in-the-Loop**: Establish approval gates for irreversible, high-stakes, or low-confidence actions
- **Orchestration over Autonomy**: Prefer deterministic workflow pipelines over fully autonomous reasoning for production systems
- **Memory & State**: Design explicit state management (task progress, context, errors) rather than relying on implicit LLM memory
- **Error Recovery**: Handle tool failures, reasoning errors, stuck loops, and partial completion gracefully

**Agent Architecture Patterns:**

| Pattern | Best For | Predictability |
|---------|----------|---------------|
| Single-agent loop | Focused tasks, prototyping | Medium |
| Multi-agent collaboration | Complex multi-domain tasks | Medium |
| Workflow agents | Production systems needing reliability | High |
| Reactive agents | Event-driven monitoring/alerting | High |

**Named Reasoning Patterns:** ReAct (reason + act with visible trace), Plan-then-Execute (upfront planning with approval), Reflexion (self-critique loop), Tree of Thought (explore multiple paths).

**Progression:** Start with workflow agents (fixed pipeline) -> add LLM branching -> add tool selection -> add planning -> full autonomy only for proven, low-risk tasks.

For deep guidance, consult `references/agent-design.md`.

---

## 2. Prompt Engineering

Prompt engineering is the discipline of crafting inputs that reliably produce desired LLM outputs. It is the primary lever for controlling AI behavior without model modification.

**Anatomy of an Effective Prompt:**
1. **Instruction**: Precise verb -- summarize, classify, extract, generate, analyze
2. **Context**: Dynamic information the LLM needs (documents, records, RAG chunks)
3. **Output Format**: Explicit format specs -- JSON schema, length constraints, tone, negative constraints
4. **Role/Persona**: Expert role for consistent perspective and domain activation
5. **Examples**: Input-output pairs demonstrating desired behavior (few-shot)

**Technique Selection:**

| Technique | When to Use | Token Impact |
|-----------|-------------|-------------|
| Zero-shot | Simple, well-defined tasks (start here) | Lowest |
| Few-shot (2-3 examples) | Format compliance, domain classification | +20-50% |
| Chain-of-thought | Reasoning, math, multi-step analysis | +50-200% output |
| Self-consistency | High-stakes reasoning (run 3-5x, majority vote) | 3-5x cost |
| Structured output mode | Machine-consumed outputs (JSON, function calls) | Lowest (replaces format instructions) |

**Development Process:** Start basic -> constrain output -> specify format -> add negative constraints -> add domain context -> consolidate -> evaluate at scale -> apply advanced techniques -> cross-model test.

**Key Insight:** Each iteration step changes one thing. This makes improvements and regressions attributable. Never change prompt and model simultaneously.

For deep guidance, consult `references/prompt-engineering.md`.

---

## 3. RAG & Grounding

RAG (Retrieval-Augmented Generation) anchors LLM outputs in factual, up-to-date, proprietary data -- the primary technique for reducing hallucinations and enabling domain-specific AI.

**Three-Step Process:**
1. **Retrieve**: Convert query to embedding, search vector database for semantically similar chunks
2. **Augment**: Inject retrieved context into prompt with explicit grounding instructions and citation requirements
3. **Generate**: LLM produces response grounded in provided factual context

**Key Design Decisions:**

| Decision | Options | Guidance |
|----------|---------|---------|
| Chunking | Fixed-size, semantic, overlapping, hierarchical | Start with 200-500 tokens, 10-20% overlap. Test 3-4 sizes. |
| Retrieval | Vector-only, hybrid (vector + keyword), multi-hop | Hybrid is best default. Multi-hop for complex questions. |
| Re-ranking | None, cross-encoder, LLM-based | Add re-ranking when precision matters more than speed. |
| Query processing | Raw query, query rewriting, HyDE, decomposition | Try query rewriting when retrieval quality is poor. |

**When RAG Is the Right Choice:**
- Proprietary or frequently updated data needed; factual accuracy critical; citations required; fine-tuning too expensive; knowledge changes regularly.

**When to Skip RAG:**
- Task uses only general knowledge; latency prohibits retrieval; knowledge fits in prompt; task is purely creative.

For deep guidance, consult `references/rag-and-grounding.md`.

---

## 4. Security & Hardening

AI systems are vulnerable to prompt injection, data leakage, and adversarial manipulation. Security must be multi-layered, not an afterthought.

**Threat Model:**
- **Direct Prompt Injection**: Malicious instructions in user input
- **Indirect Prompt Injection**: Malicious instructions in data the LLM processes (documents, web pages, tool outputs)
- **Data Leakage**: LLM revealing system prompts, PII, or sensitive context
- **Output Manipulation**: Adversarial inputs causing harmful outputs
- **Tool/Agent Abuse**: Tricking agents into misusing their tools

**Seven Defense Layers:**
1. System prompt hardening (security rules first, explicit prohibitions)
2. Input validation and sanitization (filter injection patterns, cap length, never pass raw input to tools)
3. Output validation and filtering (content moderation, PII detection, format validation, guardrail models)
4. Principle of least privilege (minimum tools, minimum data access, minimum model capability)
5. Data masking (anonymization or pseudonymization of PII before LLM processing)
6. Operational security (key management, rate limiting, monitoring, audit logging)
7. Transparency and user education (label AI interactions, disclose limitations)

**OWASP LLM Top 10:** The skill maps all 10 threats to specific defense layers. See reference file for full mapping.

**Red Teaming:** Test 50+ attack patterns before launch, after every change, and periodically. See `references/security-and-hardening.md` for methodology and compliance frameworks (GDPR, HIPAA, EU AI Act, SOC 2).

For deep guidance, consult `references/security-and-hardening.md`.

---

## 5. Evaluation & Testing

LLM outputs are probabilistic. Rigorous evaluation is essential to ensure quality, catch regressions, and compare approaches.

**Metric Categories:**

| Category | Metrics | Use For |
|----------|---------|---------|
| Text overlap | BLEU, ROUGE | Translation, summarization baselines |
| Semantic similarity | Cosine similarity, Word Mover's Distance | Meaning-preserving tasks |
| Classification | Accuracy, Precision, Recall, F1 | Categorization, extraction |
| LLM-as-Judge | Rubric-based scoring by capable LLM | Scalable quality assessment |
| Groundedness | Claim verification against sources | RAG faithfulness |
| Rule-based | JSON validity, PII absence, length bounds | Format compliance |

**Testing Strategies:** Unit testing (individual prompts) -> Integration testing (end-to-end) -> Regression testing (baseline comparison via CI/CD) -> Adversarial testing (red teaming) -> Load testing (latency, throughput, cost scaling).

**RAG Diagnostic Flow:** If answer is wrong, check faithfulness first. If faithful but wrong = retrieval problem. If unfaithful = generation problem.

**Named Frameworks:** RAGAS (RAG evaluation), DeepEval (general LLM eval), Promptfoo (prompt testing CLI), LangSmith (tracing + eval), TruLens (feedback functions).

For deep guidance, consult `references/evaluation-and-testing.md`.

---

## 6. Model Selection

No single model excels at everything. Model selection is an empirical, task-specific decision balancing capability, cost, latency, and reliability.

**Five-Step Selection Framework:**
1. Define the task precisely (classification, generation, reasoning, code, multimodal)
2. Establish evaluation criteria (accuracy on YOUR data, latency, cost, context window, privacy)
3. Benchmark empirically on 50-100 representative inputs with ground truth
4. Compare across prompting techniques (zero-shot vs. few-shot vs. CoT)
5. Full cost analysis (tokens + rate limits + engineering time + switching costs)

**Key Insight:** A cheaper model with well-crafted few-shot prompts often outperforms an expensive frontier model with zero-shot. The prompt-model combination matters more than the model alone.

**Multi-Model Strategy:** Route tasks to specialized models (cheap for classification, frontier for reasoning). Maintain fallback models. Use quality-tier routing (try cheap first, escalate on validation failure).

For deep guidance, consult `references/model-selection.md`.

---

## 7. Orchestration Patterns

Orchestration composes multiple AI capabilities into reliable, repeatable workflows -- the backbone of production AI applications.

**Standard 10-Stage Pipeline:**
User Input -> Grounding -> Templating -> Input Masking -> Input Filtering -> Input Translation -> LLM Processing -> Output Filtering -> Output Translation -> Output Delivery

**Extended Patterns:**

| Pattern | When to Use |
|---------|-------------|
| Parallel execution | Multiple independent retrievals, multi-model consensus |
| Conditional branching | Different task types need different pipelines |
| Iterative loops | Output quality validation with retry |
| Batch processing | Bulk document processing, periodic jobs |
| Streaming | User-facing apps where perceived latency matters |
| Event-driven | Webhook triggers, message queues, scheduled jobs |

**Design Principles:** Configuration-driven (JSON/YAML, not code), single API call per invocation, module composability (add/remove stages freely), stateless execution (session state injected via templating).

**Prompt Registry:** Version-controlled prompt catalog with semantic versioning, A/B testing support, and instant rollback. Prompts are code -- version, review, and test them.

For deep guidance, consult `references/orchestration-patterns.md`.

---

## 8. AI Product Lifecycle

Building AI products requires a structured progression from idea to production, with continuous monitoring and iteration.

**Five Stages:**
1. **Ideation**: Identify business value; assess LLM suitability vs. traditional code; define measurable success criteria
2. **Feasibility**: Evaluate data availability, hallucination risk tolerance, cost-benefit, ethical considerations; go/no-go checklist
3. **Prototyping**: Rapid experimentation (models, prompts, architectures); establish baselines on 50+ test cases; involve end-users early
4. **Productization**: Full development with security hardening, testing suites, monitoring, documentation; productization checklist
5. **Deployment**: Gradual rollout (shadow -> canary -> staged -> full) with stage gates; performance and quality monitoring

**Continuous Maintenance:** Model version management, prompt re-engineering on model updates, knowledge base freshness, regression testing cadence, red teaming schedule, cost drift monitoring, sunset planning.

**Decision Framework:** LLM for NL understanding/generation. Traditional code for deterministic rules. Hybrid for high-accuracy requirements. RAG + LLM for proprietary data. See reference for detailed decision table.

**Team Roles:** Product manager, AI/ML engineer, UX designer, data engineer, security engineer, domain expert, MLOps. Smaller teams overlap roles but all responsibilities need coverage.

For deep guidance, consult `references/ai-product-lifecycle.md`.

---

## Cross-Cutting Concerns

These principles apply across all 8 areas:

- **Start Simple, Iterate**: Begin with the simplest approach that could work. Add complexity only when measurement shows it is needed.
- **Measure Everything**: Token usage, latency, accuracy, cost, user satisfaction. You cannot optimize what you do not measure.
- **Separate Concerns**: Keep prompts, data, configuration, and logic independent. This enables independent iteration and testing.
- **Version Control Prompts**: Prompts are code. Version them, test them, review them, roll them back when needed.
- **Design for Failure**: LLMs are probabilistic. Every output path needs validation, fallback models, and graceful degradation.
- **Human Oversight**: For any action with real-world consequences, maintain a human approval step until the system has proven reliable at scale.
- **Responsible AI**: Consider bias, fairness, transparency, and privacy at every design decision. Test for demographic bias. Provide feedback mechanisms.
- **Cost Awareness**: Token costs scale with usage. Optimize prompts, route to appropriate model tiers, monitor cost-per-request trends.
