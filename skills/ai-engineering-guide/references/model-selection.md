# Model Selection -- Deep Reference

> Cross-references: `evaluation-and-testing.md`, `prompt-engineering.md`, `orchestration-patterns.md`, `ai-product-lifecycle.md`

---

## Selection Framework

### Step 1: Define the Task

| Task Type | Key Capabilities Needed | Example |
|-----------|------------------------|---------|
| Classification | Instruction following, consistency, structured output | Ticket routing, sentiment analysis |
| Generation | Creativity, tone control, domain knowledge | Report writing, content creation |
| Summarization | Comprehension, conciseness, faithfulness to source | Meeting notes, document digests |
| Code | Code understanding, multi-language support, debugging | Code generation, review, migration |
| Reasoning | Chain-of-thought, logical consistency, math | Data analysis, decision support |
| Extraction | Precision, schema compliance, handling missing fields | Form parsing, data entry automation |
| Conversation | Multi-turn coherence, persona consistency, memory | Customer service, co-pilots |
| Multimodal | Vision capabilities, cross-modal reasoning | Document analysis, image description |

### Step 2: Establish Evaluation Criteria

**Primary Criteria (must evaluate):**
- Accuracy on YOUR data (not generic benchmarks)
- Latency (P50 and P90 under expected load)
- Cost per token (input and output separately)
- Context window size (sufficient for your longest inputs)
- Reliability / uptime (provider SLA)

**Secondary Criteria (evaluate when relevant):**
- Multimodal support
- Fine-tuning availability
- Data privacy terms (does provider train on your data?)
- Vendor lock-in risk (how portable are your prompts?)
- Regional availability (data residency requirements)
- Structured output support (JSON mode, function calling)
- Streaming support
- Rate limits (requests/minute, tokens/minute)

### Step 3: Benchmark Empirically

Generic benchmarks (MMLU, HumanEval, GPQA) show general capability but do NOT predict performance on YOUR specific task. Build a task-specific benchmark:

**Benchmarking Process:**
1. Curate 50-100 representative inputs with ground-truth expected outputs
2. Include edge cases and difficult examples (not just easy ones)
3. Test 3-5 candidate models with identical prompts
4. Score using YOUR defined metrics (see `evaluation-and-testing.md`)
5. Analyze failure patterns per model (not just aggregate scores)
6. Consider cost-normalized performance: score per dollar

**What to Record Per Model:**

| Dimension | Metric |
|-----------|--------|
| Quality | Accuracy, F1, semantic similarity on your test set |
| Reliability | % of valid/parseable outputs, error rate |
| Speed | P50 and P90 latency |
| Cost | Cost per 1K requests at your average input/output sizes |
| Failure modes | What types of errors does each model make? |

### Step 4: Compare Across Prompting Techniques

Same model performs very differently with different prompting strategies:

| Technique | Typical Impact | Token Cost Impact |
|-----------|---------------|-------------------|
| Zero-shot | Baseline | Lowest |
| Few-shot (2-3 examples) | +10-30% accuracy on format/classification | +20-50% tokens |
| System/meta prompting | Improved consistency, minimal cost increase | +5-10% tokens |
| Chain-of-thought | +15-40% on reasoning tasks | +50-200% output tokens |
| Combined (system + few-shot + CoT) | Best quality for complex tasks | Highest cost |

**Key Finding from SAP AI Developer Curriculum:** "A cheaper model with well-crafted few-shot prompts often outperforms an expensive frontier model with zero-shot prompting." The prompt-model combination matters more than the model alone. Always test before assuming.

**Example Results (from empirical comparison):**

| Model + Technique | Valid JSON | Categories | Sentiment | Urgency |
|---|---|---|---|---|
| basic--llama3.1-70b | 100% | 83.5% | 30% | 70% |
| basic--gpt4o | 100% | 89% | 35% | 55% |
| basic--gemini-2.5-flash | 100% | 91% | 30% | 60% |
| metaprompt+fewshot--gpt4o | 100% | 91.5% | 60% | 100% |
| metaprompt+fewshot--gemini-2.5-flash | 100% | 92.5% | 55% | 90% |

Insight: The technique mattered more than the model for improving sentiment and urgency accuracy.

### Step 5: Full Cost Analysis

| Cost Factor | What to Include |
|-------------|----------------|
| Token pricing | Input tokens + output tokens (output usually 2-4x more expensive) |
| Rate limits | Hitting limits delays your application; may need higher tier |
| Engineering time | Hours to optimize prompts per model; prompt portability |
| Switching costs | If you need to change providers later, how much rework? |
| Infrastructure | Any hosting/deployment costs for self-hosted models |
| Fine-tuning | Training data preparation + training compute + evaluation |

---

## Multi-Model Strategy

### Task-Based Routing
Route different task types to the best-fit model:

| Task | Model Choice | Rationale |
|------|-------------|-----------|
| Simple classification | Lightweight, cheap model | Low complexity, high volume, cost-sensitive |
| Complex generation/reasoning | Frontier model | Quality-critical, lower volume |
| Code tasks | Code-specialized model | Domain optimization |
| Image understanding | Multimodal model | Capability requirement |
| Embeddings | Embedding-specialized model | Separate from generation |

### Fallback Strategy
Never depend on a single provider for critical applications:
- Identify and test at least one fallback model per critical task
- Design prompts that are reasonably portable across models (avoid model-specific tricks)
- Monitor provider status for automatic failover
- Test fallback path regularly (not just when primary fails)

### Quality-Tier Routing
1. First attempt with cheaper model
2. If output fails validation (format, quality threshold, confidence score), retry with more capable model
3. Track escalation rate -- high escalation means the cheap model is insufficient for this task
4. Optimize the boundary: which tasks can the cheap model handle reliably?

---

## Model Lifecycle Management

### Version Strategy

| Strategy | Behavior | Risk | Best For |
|----------|----------|------|----------|
| **Pinned version** | Lock to specific version | Must manually upgrade; may miss improvements | Production stability, regulated environments |
| **Auto-upgrade** (latest) | Always use newest version | Behavior changes without warning | Development, non-critical tasks |
| **Staged rollout** | Test new version on subset of traffic before full switch | More complex deployment | Balancing stability with staying current |

**Recommendation:** Pin versions in production. Test new versions against your full evaluation suite before upgrading. Budget 1-2 sprints per year for model migration (see `ai-product-lifecycle.md`).

### Deprecation Planning
- Monitor provider deprecation announcements (models are deprecated with notice periods)
- Maintain at least one tested fallback model
- Budget time for prompt re-optimization when switching versions or models
- Run full evaluation suite before AND after migration
- Keep a migration runbook: steps, rollback criteria, evaluation thresholds

---

## Decision Matrix Template

| Criterion | Weight | Model A | Model B | Model C |
|-----------|--------|---------|---------|---------|
| Accuracy on your dataset | 30% | ? /5 | ? /5 | ? /5 |
| Latency (P90) | 20% | ? /5 | ? /5 | ? /5 |
| Cost per 1K requests | 20% | ? /5 | ? /5 | ? /5 |
| Context window | 10% | ? /5 | ? /5 | ? /5 |
| Data privacy terms | 10% | ? /5 | ? /5 | ? /5 |
| Reliability / uptime | 10% | ? /5 | ? /5 | ? /5 |
| **Weighted Score** | **100%** | | | |

Score 1-5 per criterion, multiply by weight, sum. Makes tradeoffs explicit and decisions auditable. Update and re-run when new models become available or requirements change.

---

## Model Types

| Type | Description | When to Use |
|------|-------------|-------------|
| **Provider-managed** | Pre-integrated from third-party providers (OpenAI, Anthropic, Google). No separate infrastructure. | Default choice for most applications |
| **Self-hosted** | Deploy your own models (open-source, fine-tuned). Full control. | Data sovereignty requirements, specialized domains, cost optimization at scale |
| **Fine-tuned** | Base model adapted to your domain/task with your data | Consistent style, domain vocabulary, task-specific optimization when prompting is insufficient |

**Fine-tuning Decision:**
- Try prompting first (zero-shot, few-shot, system prompt). Fine-tuning should be a last resort, not a first step.
- Fine-tune when: prompting cannot achieve required consistency, domain-specific vocabulary is critical, you have high-quality training data, the task is high-volume (amortizes fine-tuning cost)
- Don't fine-tune when: prompting works adequately, your data is small or low quality, you need frequently updated knowledge (use RAG instead -- see `rag-and-grounding.md`)

---

## Common Mistakes

| Mistake | Why It's Wrong | What to Do Instead |
|---------|---------------|-------------------|
| Choosing based on hype/leaderboards | Generic benchmarks don't predict YOUR task performance | Benchmark on your data with your prompts |
| Frontier model for everything | 10x cost for tasks a cheap model handles equally | Task-based routing with model tiers |
| Single model, no fallback | Provider outage = your app is down | Test and maintain at least one fallback |
| Select once, never re-evaluate | New models release frequently; your choice may become suboptimal | Re-evaluate quarterly or when new models launch |
| Ignoring data privacy terms | Your data may be used for training | Read terms before sending sensitive data |
| Skipping prompt optimization per model | Different models respond differently to the same prompt | Optimize prompts per model, not just per task |
| Overlooking rate limits | Your app may need more throughput than the plan allows | Factor rate limits into architecture from day one |
