# Orchestration Patterns -- Deep Reference

> Cross-references: `prompt-engineering.md`, `rag-and-grounding.md`, `security-and-hardening.md`, `model-selection.md`, `evaluation-and-testing.md`, `agent-design.md`

---

## The Standard Pipeline

A production AI workflow composes discrete, independently configurable stages. The order ensures security, data integrity, and compliance while remaining flexible in configuration.

### 1. User Input
Raw query or trigger event. Validate type, length, format. Classify intent if handling multiple task types. Reject malformed inputs early.

### 2. Grounding (Context Retrieval)
Query vector databases for relevant documents. Apply metadata filters. Select top-K by relevance score. See `rag-and-grounding.md` for retrieval strategies, query rewriting, and re-ranking.

### 3. Templating (Prompt Construction)
Assemble the prompt from template + dynamic data + retrieved context. Use placeholders (`{{variable}}`). Store templates in version-controlled registry (see Prompt Registry section below).

### 4. Input Masking (PII Protection)
- **Anonymization**: Irreversible. Replace PII with generic placeholders.
- **Pseudonymization**: Reversible via secure mapping table. Preserves entity relationships.
Apply before LLM processing. Unmask in post-processing if pseudonymized. If masking fails, BLOCK the request -- never send unmasked PII to the LLM (see `security-and-hardening.md`).

### 5. Input Filtering (Content Safety)
Check assembled prompt for harmful, off-topic, or policy-violating content. Configurable strictness: Relaxed -> Moderate -> Strict. Filter categories: hate speech, violence, sexual content, injection attempts, excessive length.

### 6. Input Translation (Optional)
Translate to model's optimal language if the user's input is in a different language. Use when model performs better in a specific language (common with English-trained models receiving non-English input).

### 7. LLM Processing
Send assembled, filtered, masked prompt to the model. Configure: model selection (see `model-selection.md`), temperature, max tokens, top-p, stop sequences.

### 8. Output Filtering
Check response for content safety, PII leakage, format compliance, groundedness, hallucination. See `security-and-hardening.md` for filtering strategies.

### 9. Output Translation (Optional)
Translate response to user's preferred language.

### 10. Output Delivery
Return validated response to user, or trigger downstream actions (create ticket, send email, update database, invoke another pipeline).

---

## Extended Orchestration Patterns

Beyond the standard linear pipeline, production systems often need more complex flow control:

### Parallel Execution
Run multiple pipeline branches simultaneously and aggregate results:
- Use when: multiple independent retrievals needed, multi-model consensus, parallel tool calls
- Implementation: fork after user input, run branches concurrently, join before output delivery
- Aggregation strategies: merge results, majority vote, best-of-N selection, structured combination

### Conditional Branching
Route to different pipeline configurations based on input classification:
- Use when: different task types require different models, prompts, or grounding sources
- Implementation: classify input first (lightweight model or rule-based), route to appropriate pipeline branch
- Example: customer question -> knowledge base RAG pipeline; customer complaint -> sentiment analysis + escalation pipeline

### Iterative / Loop Patterns
Re-run pipeline stages based on output quality:
- Use when: output validation fails, quality threshold not met, refinement needed
- Implementation: output validator triggers re-generation with modified prompt (e.g., add "Your previous answer was rejected because [reason]. Try again with...")
- Guard: max iteration limit to prevent infinite loops (typically 2-3 retries max)

### Batch Processing
Process multiple inputs through the pipeline efficiently:
- Use when: bulk document processing, periodic report generation, batch classification
- Implementation: queue inputs, process with rate limiting, aggregate results
- Considerations: respect API rate limits (implement `RateLimitedIterator`), handle partial failures gracefully, enable resumption from failure point

### Streaming
Stream LLM output tokens to the user as they generate:
- Use when: user-facing applications where perceived latency matters
- Considerations: output filtering must handle partial output or apply post-stream; PII detection on partial output is harder; streaming breaks atomic output validation
- Pattern: stream to user + buffer for validation; if validation fails post-generation, show correction

### Event-Driven / Async Patterns
Trigger pipeline execution from external events:
- Use when: webhook triggers, scheduled jobs, message queue processing, monitoring alerts
- Implementation: event listener -> input normalization -> standard pipeline -> result routing
- Example: new support ticket event -> classify + respond pipeline -> route to agent or auto-reply

---

## Design Principles

### Configuration-Driven
Define workflows as JSON/YAML configuration, not imperative code. Benefits:
- Non-developer modification (product managers can adjust filtering levels)
- Version control and diff-ability
- A/B testing (swap configurations, not code)
- Rapid iteration without code deployments

**Configuration Example Structure:**
```
pipeline:
  grounding:
    enabled: true
    data_repositories: ["kb-product-docs", "kb-policies"]
    max_chunk_count: 5
  templating:
    template_id: "customer-support-v3"
    defaults:
      tone: "professional"
      language: "en"
  masking:
    enabled: true
    entities: ["email", "phone", "name"]
    method: "pseudonymization"
  input_filtering:
    enabled: true
    level: "moderate"
  llm:
    model: "gpt-4o"
    temperature: 0.3
    max_tokens: 1024
  output_filtering:
    enabled: true
    level: "moderate"
```

### Single API Call
One API call triggers the entire pipeline. The caller does not need to know about internal stages. Simplifies integration: consumer sends input, receives output, internal orchestration is abstracted.

### Module Composability
Each module is independently configurable and optional. Need grounding? Enable it. No PII concerns? Disable masking. Add or remove modules without rewriting the pipeline. Each module has its own error handling.

### Stateless Execution
Each invocation is stateless. The pipeline has no memory between calls. Session state (conversation history, user preferences) is injected via templating, managed externally. This enables horizontal scaling and simplifies debugging.

---

## Prompt Registry & Version Management

### Why a Registry
- **Consistency**: All applications use approved, tested prompt versions
- **Auditability**: Full history of what prompts were used when (required for compliance)
- **Reusability**: Share prompts across teams and applications
- **A/B testing**: Run multiple prompt versions simultaneously against live traffic
- **Rollback**: Quickly revert if quality degrades after a prompt change

### Registry Interfaces
- **Imperative API** (design-time): CRUD operations for creating and iterating on prompts during development
- **Declarative API** (CI/CD): Git-based "prompts as code." Prompts versioned alongside application code. Changes deployed via pull request + review + automated testing.

### Template Schema

| Component | Purpose | Example |
|-----------|---------|---------|
| Template body | Message roles with placeholders | `"Classify this {{input_type}}: {{user_input}}"` |
| Defaults | Default values for optional placeholders | `{tone: "professional", language: "en"}` |
| Metadata | Owner, model target, description | `{owner: "support-team", model: "gpt-4o"}` |
| Version | Semantic versioning | `2.1.0` (major.minor.patch) |
| Validation rules | Expected output format, required fields | `{format: "json", required: ["category", "sentiment"]}` |

### Prompt Retrieval Patterns
- **By unique ID**: Immutable, exact version. Use for production (deterministic behavior).
- **By name + version**: Specific iteration. Use for staged rollouts.
- **By name alone**: Latest version. Use for development and testing only.

---

## Error Handling

### Per-Module Error Strategies

| Module | Failure Scenario | Strategy |
|--------|-----------------|----------|
| Grounding/Retrieval | No relevant documents found | Return empty context with flag; respond with "I don't have information on that" |
| Grounding/Retrieval | Vector DB timeout | Retry once; if still failing, proceed without grounding with disclaimer |
| Masking | Masking service unavailable | BLOCK the request -- never send unmasked PII to LLM |
| LLM | Timeout or rate limit | Retry with exponential backoff; fall back to simpler/different model |
| LLM | Content refused by model | Log refusal, return safe generic response, alert for review |
| Output Filtering | Output blocked by safety filter | Return safe generic response; log for analysis of filter calibration |
| Translation | Translation service failure | Return in original language rather than failing entirely |

### Circuit Breaker Pattern
If a module fails repeatedly within a time window:
1. **Closed** (normal): All requests pass through
2. **Open** (tripped): Bypass the failing module, route through degraded path
3. **Half-open** (testing): Periodically send test requests to check recovery
4. **Closed** (recovered): Resume normal operation

**Thresholds:** Configure per module. Example: 5 failures in 60 seconds -> open circuit for 5 minutes.

### Fallback Chains
Progressive degradation for LLM processing:
1. Primary model (frontier) -> 2. Secondary model (fallback) -> 3. Cached response (if available) -> 4. Generic error message

Each fallback level should be tested and monitored. Track how often each level is reached.

---

## Monitoring

### Per-Module Metrics

| Metric | What It Shows |
|--------|--------------|
| Latency per module | Bottleneck identification |
| Error rate per module | Component reliability |
| Filter rejection rate | Filter calibration (too strict? too loose?) |
| Retrieval relevance scores | RAG quality |
| Masking accuracy | PII protection effectiveness |

### Pipeline-Level Metrics

| Metric | What It Shows |
|--------|--------------|
| End-to-end latency | User experience |
| Success rate | Overall reliability |
| Token usage per request | Cost tracking |
| Cost per request | Budget management |
| Throughput (requests/sec) | Capacity utilization |

### Quality Metrics
- User satisfaction (feedback scores)
- Output accuracy (automated + human evaluation, see `evaluation-and-testing.md`)
- Groundedness scores (for RAG pipelines)
- Escalation rate (how often does output need human review?)

### Tracing
Enable JSON trace of entire pipeline execution for debugging:
- Input received -> each module's input/output -> final response
- Trace ID per request for end-to-end correlation
- Log trace for failed or flagged requests; sample for successful requests
- Essential for debugging "why did this request produce that output?"

---

## Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| **Monolithic prompts** | One massive prompt trying to do everything in one LLM call | Decompose into pipeline stages; use orchestration |
| **No error handling** | Assuming every module succeeds | Implement per-module error strategies + circuit breakers |
| **Hardcoded config** | Model names, parameters embedded in code | Use configuration files; environment-specific configs |
| **No per-module observability** | Cannot identify which module is causing issues | Add latency/error/quality metrics per module |
| **Over-engineering** | Adding modules "just in case" (each adds latency) | Start minimal, add modules when measurement shows need |
| **No prompt versioning** | Cannot reproduce or rollback prompt changes | Use prompt registry with semantic versioning |
| **Tight module coupling** | Changing one module breaks others | Define clear interfaces between modules; test independently |
| **No testing of error paths** | Only test happy path | Test each module's failure mode; inject faults |
| **Ignoring cold start** | First request after deployment is slow | Warm up models and connections; monitor cold start latency |
