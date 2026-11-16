# Evaluation & Testing -- Deep Reference

> Cross-references: `prompt-engineering.md`, `rag-and-grounding.md`, `agent-design.md`, `model-selection.md`, `security-and-hardening.md`, `ai-product-lifecycle.md`

---

## Why LLM Evaluation Is Different

Unlike traditional software where outputs are deterministic, LLMs introduce probabilistic variability. The same prompt can produce different outputs across runs. Evaluation must account for this by:
- Testing at scale (50-200+ examples, not 1-2)
- Using multiple metrics (not a single score)
- Measuring distribution of quality, not just averages
- Comparing against baselines, not just absolute thresholds

---

## Quantitative Metrics

### Text Overlap Metrics
- **BLEU**: N-gram precision vs. reference text. For translation/generation. Range 0-1. Limitation: misses synonyms and paraphrases. Best used alongside semantic metrics.
- **ROUGE**: N-gram recall vs. reference. For summarization. Variants: ROUGE-1 (unigrams), ROUGE-2 (bigrams), ROUGE-L (longest common subsequence). Same synonym limitation as BLEU.

### Semantic Similarity
- **Cosine Similarity**: Embed both texts, measure angle between vectors. Captures meaning regardless of wording. Range -1 to 1. Requires embedding model. Most practical semantic metric.
- **Jaccard Index**: Token set overlap (intersection/union). Simple but ignores word order and semantics. Useful as a cheap complementary check.
- **Word Mover's Distance**: Minimum "travel cost" between word embeddings. More nuanced than cosine but computationally expensive. Good for research, less practical for production eval.

### Classification Metrics
- **Accuracy**: Correct / total. Misleading with imbalanced classes (99% accuracy if 99% of data is one class).
- **Precision**: True positives / predicted positives. High precision = few false positives. Optimize when false positives are costly.
- **Recall**: True positives / actual positives. High recall = few false negatives. Optimize when false negatives are costly.
- **F1 Score**: Harmonic mean of precision and recall. Best balanced single metric for classification tasks.
- **Confusion Matrix**: Full breakdown of TP, TN, FP, FN per class. Essential for understanding error patterns.

### LLM-as-Judge
Use a capable LLM to score another LLM's output against defined rubrics. Scales well across large evaluation sets. Not deterministic -- validate against human judgments on a calibration set (50-100 examples). Use a more capable model as judge than the model being evaluated.

**Rubric Design:**
- Define 3-5 dimensions (relevance, accuracy, completeness, tone, format compliance)
- Use a 1-5 scale per dimension with concrete descriptions for each level
- Provide 2-3 scored examples as calibration (few-shot for the judge)
- Request reasoning before the score (chain-of-thought improves consistency)

### Groundedness (RAG-specific)
For RAG systems: verify every claim in the response is supported by retrieved context.

**Approaches:**
- Claim extraction: break response into individual claims, check each against context
- NLI entailment scoring: use a natural language inference model to classify claim-context pairs as entailed/contradicted/neutral
- Citation accuracy: verify that cited sources actually support the claims attributed to them

### Rule-Based Checks
Deterministic validations -- fast, reliable, complement LLM-based metrics:
- JSON/XML validity and schema compliance
- Required field presence and type checking
- Keyword presence/absence (e.g., must include disclaimer, must not include PII)
- Length bounds (min/max characters or tokens)
- Format patterns (dates, emails, phone numbers)
- Language detection (response in expected language)

---

## RAG-Specific Evaluation

| Metric | What It Measures | Diagnostic Value |
|--------|-----------------|-----------------|
| Context Relevance | Are retrieved chunks relevant to query? | Low = retrieval problem |
| Context Recall | Does context contain info needed to answer? | Low = coverage problem |
| Faithfulness | Is answer supported by context? | Low = generation problem |
| Answer Relevance | Does answer address the query? | Low = instruction problem |
| Answer Correctness | Is answer factually correct? | Low = end-to-end problem |

**Diagnostic flow:** If answer is wrong, check faithfulness first. If faithful but wrong, the problem is retrieval. If unfaithful, the problem is generation. See `rag-and-grounding.md` for RAG evaluation details.

---

## Qualitative Methods

### Expert Review
Domain specialists rate outputs on defined dimensions (accuracy, completeness, tone, safety). Expensive but highest fidelity. Use for:
- Establishing initial baselines
- Validating automated metrics (do automated scores correlate with expert judgment?)
- High-stakes evaluation (medical, legal, financial outputs)

### User Feedback
- **Thumbs up/down**: High volume, low signal per data point. Useful for trend detection.
- **Star ratings**: Moderate signal. Better for comparative analysis.
- **Free-text comments**: Rich but hard to aggregate. Use NLP to categorize.
- **Implicit signals**: Follow-up question rate (high = initial answer insufficient), task abandonment rate, time-to-next-action.

### A/B Testing
Split users into groups receiving different system versions. Compare prompts, models, RAG configurations, or orchestration settings.
- Requires sufficient volume for statistical significance
- Change only ONE variable at a time (prompt OR model, not both)
- Run for adequate duration (minimum 1-2 weeks for enterprise apps)
- Track both quality metrics AND user behavior metrics

---

## Testing Strategies

### Unit Testing
- Test individual prompt templates with known inputs vs. expected outputs
- Test each tool integration independently (mock external services)
- Test retrieval precision/recall separately from generation quality
- Test input validation and output filtering rules independently

### Integration Testing
- End-to-end: user input -> retrieval -> prompt construction -> LLM -> output validation -> delivery
- Verify all orchestration modules work together (see `orchestration-patterns.md`)
- Use realistic data -- not synthetic toy examples
- Test error paths: what happens when retrieval returns nothing? When LLM times out? When filtering blocks the output?

### Regression Testing
- Maintain baseline dataset of prompt-output pairs (golden dataset)
- Run after every prompt, model, configuration, or data change
- Flag deviations from baseline (score drops, format changes, new failure patterns)
- Automate via CI/CD: every commit triggers evaluation pipeline

### Adversarial Testing (Red Teaming)
- Prompt injection attempts (direct and indirect)
- Boundary conditions: very long inputs, empty inputs, special characters, unicode edge cases
- Bias testing: evaluate across diverse demographic inputs
- Out-of-scope requests: verify graceful refusal
- See `security-and-hardening.md` for detailed red teaming methodology

### Load & Stress Testing
- Measure latency under concurrent load (P50, P90, P99 percentiles)
- Find throughput limits (requests/second before degradation)
- Verify graceful degradation under overload (fallback models, queue management)
- Test rate limiting behavior
- Measure cost scaling (does cost grow linearly or super-linearly with load?)

---

## Evaluation Function Design

Standard structure for automated evaluation:

```
function evaluate(input, generated_output, ground_truth):
    results = {}
    
    # 1. Parse: extract structured data from output
    parsed = parse_output(generated_output)
    
    # 2. Rule-based checks
    results["valid_format"] = check_format(parsed)
    results["required_fields"] = check_fields(parsed)
    
    # 3. Content metrics
    results["accuracy"] = compare_to_ground_truth(parsed, ground_truth)
    results["completeness"] = check_completeness(parsed, ground_truth)
    
    # 4. Semantic metrics
    results["semantic_similarity"] = cosine_sim(embed(generated_output), embed(ground_truth))
    
    return results
```

**Execution guidance:**
- Run across representative datasets (50-200+ examples minimum)
- Respect API rate limits (implement rate-limited iteration)
- Aggregate results: mean, median, standard deviation, worst-case percentile
- Track per-category performance (not just overall averages -- some categories may degrade while overall looks fine)

---

## Agent-Specific Evaluation

| Dimension | Metric | Method |
|-----------|--------|--------|
| Task completion | Success rate | Automated task suite with expected outcomes |
| Efficiency | Steps per task, tokens per task | Instrumented benchmarks |
| Tool selection | Correct tool for each step | Annotated ground truth per step |
| Error recovery | Recovery rate from injected failures | Chaos/fault injection testing |
| Safety | Boundary violation rate | Adversarial testing |
| Planning quality | Plan optimality vs. expert plans | Expert comparison |

See `agent-design.md` for agent-specific evaluation considerations.

---

## Named Evaluation Frameworks

| Framework | Focus | Key Features |
|-----------|-------|-------------|
| **RAGAS** | RAG evaluation | Faithfulness, answer relevance, context precision/recall |
| **DeepEval** | General LLM evaluation | 14+ metrics, supports custom metrics, CI/CD integration |
| **Promptfoo** | Prompt testing | CLI tool, YAML test definitions, model comparison, CI/CD |
| **LangSmith** | Tracing + evaluation | End-to-end traces, annotation queues, dataset management |
| **OpenAI Evals** | Model evaluation | Extensible framework, community benchmarks |
| **TruLens** | Feedback functions | Groundedness, relevance, moderation scoring |

**Selection guidance:** Start with Promptfoo for prompt-level testing (lightweight, fast iteration). Add RAGAS for RAG-specific metrics. Use LangSmith or equivalent for production tracing and ongoing monitoring.

---

## MLOps for Continuous Evaluation

- **Automated benchmarking**: Run evaluation suite on every prompt/model/config change via CI/CD pipeline
- **Centralized logging**: Track all metrics over time with dashboards. Detect trends and regressions.
- **Error categorization**: Maintain running tallies of failure types -- hallucination rate, format failure rate, jailbreak success rate, retrieval miss rate
- **Gradual rollouts**: Shadow mode (compare silently) -> canary (small % of traffic) -> staged rollout -> full deployment
- **Alerting**: Metric drops beyond thresholds trigger alerts. Error rate spikes. Latency increases. Cost per request anomalies.
- **Feedback loops**: Route user feedback to evaluation dashboards. Correlate user satisfaction with automated metrics.

---

## Performance & Operational Metrics

Track alongside quality metrics:

| Metric | What to Track | Why |
|--------|--------------|-----|
| Latency | P50, P90, P99 per request | User experience, SLA compliance |
| Throughput | Requests/second | Capacity planning |
| Token usage | Input + output tokens per request | Cost optimization |
| Error rate | Failed requests / total requests | Reliability |
| Cost per request | Token cost + infrastructure cost | Budget management |
| Retrieval latency | Time for RAG retrieval step | RAG pipeline optimization |
| Cache hit rate | Cached responses / total | Efficiency indicator |

**Cost Tracking Insight:** Evaluate the cost-quality tradeoff explicitly. A model that scores 5% higher but costs 10x more may not be the right choice. Always benchmark cost alongside quality (see `model-selection.md`).
