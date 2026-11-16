# Prompt Engineering -- Deep Reference

> Cross-references: `rag-and-grounding.md`, `evaluation-and-testing.md`, `model-selection.md`, `orchestration-patterns.md`, `security-and-hardening.md`

---

## Five Components of an Effective Prompt

### 1. Instruction (The Verb)
Use precise verbs: summarize, classify, extract, generate, translate, compare, analyze, rewrite.
Avoid vague instructions like "help with" or "do something about."

**Verb Selection Guide:**

| Task Type | Strong Verbs | Avoid |
|-----------|-------------|-------|
| Information extraction | Extract, identify, list, parse | "Find" (ambiguous) |
| Content creation | Generate, write, compose, draft | "Make" (vague) |
| Analysis | Analyze, compare, evaluate, assess | "Look at" |
| Transformation | Summarize, translate, rewrite, convert | "Change" |
| Classification | Classify, categorize, label, rate | "Sort" (ambiguous) |

### 2. Context (Input Data)
Dynamic information the LLM needs: documents, records, conversation history, RAG-retrieved chunks.
Use clear delimiters (XML tags, triple backticks, headers) to separate context from instruction.
Principle: The LLM can only reason about what it can see. Omitted context = guessing.

### 3. Output Format
Specify structure (JSON schema, bullet points, table, markdown), length limits, tone, and negative constraints ("Do NOT include markdown code fences").

**Format Specification Checklist:**
- Structure: JSON, XML, markdown, plain text, table?
- Schema: exact field names, types, nesting for structured output
- Length: min/max words, sentences, or tokens
- Tone: formal, conversational, technical, simplified
- Language: output language if different from input
- Negative constraints: what to exclude ("no markdown", "no preamble")

### 4. Role / Persona
Assign an expert role to activate relevant knowledge patterns. Include domain, perspective, and what the role would never do. Place in the system message for persistence across turns.

### 5. Examples (Few-Shot)
1-5 input-output pairs demonstrating the desired behavior. Cover edge cases, not just happy paths. Wrap in clear delimiters. Order from simple to complex. Choose diverse, representative examples.

---

## Core Techniques

### Zero-Shot
Direct instruction, no examples. Best for simple, well-defined tasks. Minimal tokens. May produce inconsistent formatting. Use as your baseline -- only add complexity when zero-shot is insufficient.

### Few-Shot (1-5 examples)
Dramatically improves format compliance and domain-specific classification. More tokens per request. Diminishing returns beyond 5 examples. Choose diverse, representative examples covering edge cases.

**Few-Shot Example Structure:**
```
<Example>
  <Input>[representative input]</Input>
  <Output>[exact desired output format]</Output>
</Example>
```

**Selection Criteria for Examples:**
- Cover the range of expected inputs (not just easy cases)
- Include at least one edge case (missing data, ambiguous input)
- Demonstrate the exact output format you expect
- Use real or realistic data, not obviously fake placeholders

### Meta / System Prompting
Persistent instruction defining persona, rules, constraints, safety boundaries, and output defaults. Place in the system message. Security-critical rules go first (primacy effect). Reduces concept drift in multi-turn conversations.

**System Prompt Structure Pattern:**
```
1. IDENTITY: Who the LLM is (role, domain, perspective)
2. SECURITY RULES: What it must never do (see security-and-hardening.md)
3. TASK CONSTRAINTS: Scope, limitations, guardrails
4. OUTPUT FORMAT: Default format, language, tone
5. FALLBACK BEHAVIOR: What to do when uncertain or when input is out of scope
```

### Chain-of-Thought (CoT)
"Think step-by-step before answering." Significantly improves accuracy on reasoning, math, multi-step analysis, and complex classification. Increases output tokens and latency. Not needed for simple, direct tasks.

**When CoT Helps Most:**
- Math and logic problems
- Multi-step reasoning (cause-effect chains)
- Complex classification requiring justification
- Tasks where the reasoning process matters as much as the answer

### Self-Consistency
Run the same CoT prompt multiple times (3-5), collect different reasoning paths, take the majority answer. Improves reliability on complex reasoning tasks. Costs scale linearly with number of runs.

**Use when:** High-stakes reasoning where a single CoT run may reach wrong conclusions. The consensus answer across multiple runs is more reliable than any single run.

### Structured Output Mode
Many models support forced structured output (JSON mode, function calling, tool use schemas). When available, use these instead of prompt-based format instructions:
- Guarantees valid JSON/schema compliance
- Eliminates format parsing failures
- Reduces prompt tokens (no need for format instructions)
- More reliable than prompt-based formatting for machine-consumed outputs

### Combining Techniques
Techniques are composable: system prompt + few-shot + CoT can be used together. But more complexity is not always better -- empirical testing sometimes shows simpler approaches outperform complex ones. Always measure before committing to a complex approach (see `evaluation-and-testing.md`).

**Technique Selection Decision Tree:**
1. Try zero-shot first (baseline)
2. If format compliance fails -> add few-shot examples
3. If reasoning quality fails -> add chain-of-thought
4. If consistency fails -> add self-consistency (multiple runs)
5. If context drift in multi-turn -> strengthen system prompt
6. At each step, measure improvement vs. added cost

---

## Conversational Roles

### System Role
First message in the API call. Defines persona, rules, boundaries, output defaults. Static per application.

**Structure:** Identity -> Security rules -> Task constraints -> Output format -> Fallback behavior.

### User Role
Dynamic per-turn content from: end-user input, application logic, RAG-retrieved context. Always separate raw user input from injected context using delimiters. Validate and sanitize user input before injection (see `security-and-hardening.md`).

### Assistant Role
LLM's prior responses. Provides conversational memory for multi-turn coherence. Developer manages the message history: append responses, truncate or summarize when context window fills. Without it, each turn is isolated.

### Message List Management
API calls send chronological `[{role, content}, ...]`. As conversations grow, manage context window:
- **Sliding window**: Keep last N turns, drop oldest
- **Summarization**: Periodically summarize history, replace detailed turns with summary
- **Selective retention**: Keep system prompt + most recent turns + key earlier turns
- **Hybrid**: Summarize old turns, keep recent in full detail

---

## Iterative Prompt Development

1. **Start basic** -- simplest possible prompt, observe output
2. **Constrain output** -- add categories, field names, length limits
3. **Specify format** -- JSON schema, no extra text, strict typing
4. **Add negative constraints** -- "Do not include...", "If missing, return null"
5. **Add domain context** -- business-specific terminology, valid category lists
6. **Consolidate** -- merge refinements into single clean prompt
7. **Evaluate at scale** -- run against 50+ representative examples, establish baseline metrics (see `evaluation-and-testing.md`)
8. **Apply advanced techniques** -- few-shot, CoT as needed to address specific weaknesses identified in evaluation
9. **Cross-model test** -- same prompt on 3-5 candidate models (see `model-selection.md`)

**Principle:** Each step changes one thing. This makes improvements and regressions attributable. Never change prompt and model simultaneously.

---

## Prompt Templates

### Placeholder Pattern
Use `{{variable_name}}` for dynamic content injection. Separate template definition from runtime data. Version templates like code (see `orchestration-patterns.md` for registry patterns). Support A/B testing between template versions.

### Structural Tags
Use XML-like tags for complex prompts:

```
<Instructions>
  Classify the customer complaint and extract key information.
</Instructions>

<OutputFormat>
  Return JSON with fields: category, sentiment, urgency, summary
</OutputFormat>

<Examples>
  <Example>
    <Input>My order #12345 arrived damaged</Input>
    <Output>{"category": "shipping", "sentiment": "negative", "urgency": "high", "summary": "Damaged order received"}</Output>
  </Example>
</Examples>

<UserQuery>
  {{user_input}}
</UserQuery>
```

Tags create unambiguous boundaries the LLM can parse reliably. They also help with security by clearly separating trusted instructions from untrusted input.

### Prompt Registry
Centralized catalog of production prompts with metadata (owner, model target, last tested, performance metrics). Git-based versioning. Code review for changes. Regression tests on every update. See `orchestration-patterns.md` for registry architecture.

---

## Prompt Optimization

### Token Efficiency
- Remove redundant instructions (LLMs understand concise directives)
- Use abbreviations in schema definitions where unambiguous
- Move static context to system prompt (sent once per session, not per turn)
- For high-volume systems, a 20% prompt reduction = 20% cost reduction

### Temperature and Sampling Parameters
- **Temperature**: Controls randomness. 0 = deterministic (classification, extraction). 0.3-0.7 = balanced (general generation). 0.8-1.0 = creative (brainstorming, writing).
- **Top-p**: Nucleus sampling. 0.9 is a common default. Lower = more focused output.
- **Max tokens**: Set a ceiling to prevent runaway generation. Size to expected output + buffer.
- **Stop sequences**: Define strings that halt generation (e.g., `"\n\n"` to stop after one section).

### Multimodal Prompting
When combining text and images: explicitly instruct the LLM to analyze both. Describe what the image contributes that text alone cannot. Use for visual verification, document analysis, diagram interpretation, UI review.

---

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| Vague instructions without specific verbs | Inconsistent, unfocused outputs | Use precise action verbs (extract, classify, summarize) |
| Missing output format specification | Unparseable outputs, inconsistent structure | Always specify format, schema, and constraints |
| Too many examples (>5) | Diminishing returns, increased cost | Use 2-3 diverse examples; add more only if measured improvement |
| Not testing across models | Prompt optimized for one may fail on another | Test on 3-5 models (see `model-selection.md`) |
| Prompts hardcoded in application code | Unversioned, untestable, hard to iterate | Use templates in a version-controlled registry |
| No negative constraints | LLM adds unwanted content (preambles, disclaimers) | Explicitly state what to exclude |
| Ignoring token cost at scale | Budget overruns on high-volume systems | Profile token usage, optimize prompt length |
| Changing prompt and model simultaneously | Cannot attribute improvement or regression | Change one variable at a time, measure each |
