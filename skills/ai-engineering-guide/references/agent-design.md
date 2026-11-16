# AI Agent Design & Architecture -- Deep Reference

> Cross-references: `prompt-engineering.md`, `orchestration-patterns.md`, `security-and-hardening.md`, `evaluation-and-testing.md`, `model-selection.md`

---

## Agent Architecture Patterns

### Single-Agent Loop
One LLM with tools, iterating: Receive task -> Reason -> Select tool -> Execute -> Observe result -> Repeat until done.
**Best for:** Focused tasks (research, document processing, code generation). Simple to debug and monitor.
**Risks:** Infinite loops, error accumulation, context window exhaustion.
**Mitigate with:** Max iteration limits, token budgets, explicit termination criteria, progress tracking.

### Multi-Agent Collaboration
Orchestrator decomposes tasks, assigns to specialized worker agents, synthesizes results.
**Best for:** Complex tasks spanning multiple domains. Enables parallelism and specialization.
**Design:** Clear interfaces between agents. Workers don't need full task context. Orchestrator handles failures and aggregation.
**Example:** Research agent gathers data -> Analysis agent interprets -> Writing agent composes report -> Review agent validates.

### Workflow Agents (Recommended for Production)
Fixed-sequence pipeline with LLM decision points at specific stages. Overall flow is deterministic; LLM handles judgment within each stage.
**Best for:** Production systems requiring predictability, auditability, reliability.
**Advantage:** Each stage independently testable. Failures localized. Easy to reason about. See `orchestration-patterns.md` for pipeline design.

### Reactive Agents
Event-driven: listen for triggers, analyze event, select from predefined action set, execute.
**Best for:** Monitoring, alerting, automated response systems, real-time classification.

### Named Reasoning Patterns

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **ReAct** (Reason + Act) | Interleave reasoning traces with tool actions. LLM explains its thinking before each action. | Complex tasks needing audit trail and debugging visibility |
| **Plan-then-Execute** | LLM creates full plan upfront, then executes steps sequentially. Plan can be reviewed/approved before execution. | Tasks where upfront planning prevents wasted work; human-in-the-loop approval |
| **Reflexion** | After task completion, LLM reviews its own output and iterates. Self-critique loop. | Quality-critical outputs; writing, analysis, code review |
| **Tree of Thought** | Explore multiple reasoning paths in parallel, evaluate, prune bad branches. | Problems with multiple valid approaches where the best path is unclear |

**Choosing a Pattern:**
- Need transparency? -> ReAct (reasoning is visible)
- Need human approval before execution? -> Plan-then-Execute
- Need highest output quality? -> Reflexion (self-critique)
- Uncertain problem space? -> Tree of Thought (explore alternatives)
- Production reliability? -> Workflow Agent (deterministic flow)

---

## Core Design Principles

### 1. Tool Design
Tools are how agents interact with the world. Quality of tool descriptions directly impacts agent effectiveness.

**Each tool needs:**
- Clear name (verb-noun: `search_knowledge_base`, `create_task`, `get_order_status`)
- Precise description of what it does, when to use it, and what it returns
- Typed parameters with validation and clear constraints
- Informative error messages the LLM can reason about (not raw stack traces)
- Idempotency where possible (safe to retry)

**Principle of Minimum Toolset:** An agent with 5 well-designed tools outperforms one with 50 poorly-scoped tools. Grant minimum tools needed. Each additional tool increases selection confusion and error surface.

**Tool Description Example:**
```
Name: search_knowledge_base
Description: Search the internal knowledge base for documents relevant 
  to a query. Use when the user asks a question about company policies, 
  procedures, or product documentation. Returns up to 5 ranked results 
  with title, snippet, and relevance score.
Parameters:
  - query (string, required): Natural language search query
  - category (string, optional): Filter by category (hr, engineering, product)
  - max_results (integer, optional, default: 5): Number of results (1-20)
Returns: Array of {title, snippet, score, document_id}
Errors: "NO_RESULTS" if nothing found, "INVALID_CATEGORY" if filter unrecognized
```

### 2. Human-in-the-Loop
Define explicit approval gates for:
- Irreversible actions (deleting data, sending communications, financial transactions)
- High-stakes decisions (security changes, production deployments)
- Low-confidence situations (agent uncertainty detected)

**Implementation Patterns:**

| Pattern | Description | Use When |
|---------|-------------|----------|
| **Pre-action approval** | Agent proposes action, waits for human confirmation | Irreversible or high-cost actions |
| **Confidence-threshold autonomy** | Agent acts autonomously above confidence threshold, escalates below | Varying risk levels within same workflow |
| **Tiered classification** | Actions categorized as safe/risky/prohibited; rules per tier | Clear risk taxonomy exists |
| **Post-action review** | Agent acts, human reviews and can undo | Time-sensitive + reversible actions |

### 3. Memory & State Management
Never rely on implicit LLM "memory." Design explicit state:
- **Task state**: Progress, completed steps, remaining work, decisions made
- **Context state**: Gathered information, tool results, retrieved documents
- **Error state**: Failures encountered, retries attempted, degraded capabilities
- **Conversation state**: Prior turns, user preferences, session context

**Memory Types:**

| Type | Scope | Implementation | Example |
|------|-------|---------------|---------|
| **Working memory** | Single task | In-context (prompt injection) | Current conversation + retrieved docs |
| **Short-term memory** | Session | Structured state object (JSON) | Task progress, tool results |
| **Long-term memory** | Cross-session | External storage (database, vector store) | User preferences, past interactions |
| **Episodic memory** | Historical | Summarized past experiences | "Last time this query type failed because..." |

**State Management Strategies:**
- In-context: Simple but context-expensive. Append everything to messages. Works for short tasks.
- Structured JSON state: Efficient, debuggable. Explicit object tracking progress, results, errors. Best for multi-step agents.
- External storage: For long-running or cross-session tasks. Persist to database. Enables resumption after failures.

### 4. Planning Strategies

| Strategy | Description | Tradeoff |
|----------|-------------|----------|
| **No planning** | Act immediately on each input | Fast but may backtrack |
| **Single-step lookahead** | Consider next action only | Low overhead, moderate quality |
| **Full plan generation** | Create complete plan before acting | Higher quality, risk of stale plans |
| **Adaptive replanning** | Plan, execute, replan after each step | Best quality, highest cost |

For most production systems, **single-step lookahead** or **adaptive replanning** balances quality and cost. Full upfront planning works best with human review gates.

### 5. Error Recovery
- **Tool failures**: Retry with exponential backoff, try alternative tools, graceful degradation
- **Reasoning errors**: Validate tool-call arguments before execution; use schema validation
- **Stuck loops**: Detect repeated identical actions (3+ same tool call = stuck); enforce iteration limits
- **Partial completion**: Save progress, report what was accomplished vs. what remains, enable resumption
- **Context overflow**: Summarize prior context, drop least relevant information, prioritize recent and task-critical data

### 6. Observability
Log every LLM call, tool invocation, decision point, and state transition. Assign trace IDs per task for end-to-end debugging.

**What to Track:**

| Metric | Why |
|--------|-----|
| Tool call success/failure rates | Identify unreliable integrations |
| Reasoning step count per task | Detect efficiency regressions |
| Token usage per task | Cost optimization |
| Task completion rate | Overall agent effectiveness |
| Human escalation rate | Autonomy calibration |
| Time-to-completion | User experience |
| Error recovery success rate | Resilience measurement |

---

## Agent Prompt Design

An agent's system prompt needs:
1. **Identity and purpose** -- what is this agent, what is its mission
2. **Available tools** -- descriptions, when to use each, what they return
3. **Decision framework** -- how to choose between tools, when to ask for help vs. act
4. **Output protocol** -- how to format tool calls, how to present results to user
5. **Boundaries** -- what the agent must never do (see `security-and-hardening.md`)
6. **Error handling** -- what to do when things go wrong (retry? escalate? inform user?)
7. **Termination criteria** -- how to know when the task is complete

**Prompt Structure Pattern:**
```
IDENTITY: You are [role] that [purpose].

TOOLS: You have access to:
- [tool_1]: [description]. Use when [condition].
- [tool_2]: [description]. Use when [condition].

WORKFLOW:
1. [First step with decision criteria]
2. [Second step]
...

RULES:
- Never [prohibited action]
- Always [required behavior]
- If uncertain, [escalation behavior]

COMPLETION: Task is complete when [criteria]. Summarize what was done.
```

---

## Safety Guardrails

- **Scope boundaries**: Explicit allow/deny lists for agent actions
- **Resource limits**: Max iterations, token budget, time budget, tool call count per task
- **Output validation**: Validate LLM tool-call arguments BEFORE execution (schema check, range check, permission check)
- **Sandboxing**: Isolate code execution, restrict file system and network access
- **Audit trail**: Log all actions for review and incident investigation
- **Rate limiting**: Prevent runaway agents from overwhelming external services
- **Kill switch**: Ability to halt agent mid-execution in emergencies

---

## Agent Evaluation

| What to Evaluate | Metric | Method |
|-----------------|--------|--------|
| Task completion | Success rate on representative tasks | Automated test suite |
| Efficiency | Steps/tokens per task vs. baseline | Benchmark comparison |
| Tool selection | Correct tool chosen for each step | Ground truth annotation |
| Error handling | Recovery rate from injected failures | Chaos testing |
| Safety | Boundary violation rate | Adversarial testing (see `security-and-hardening.md`) |
| User satisfaction | Feedback scores, task completion without correction | User studies, A/B testing |

See `evaluation-and-testing.md` for detailed metric definitions and testing strategies.

---

## From Prototype to Production

1. **Start with workflow agents** (fixed pipeline) -- predictable, easy to test
2. **Add LLM branching** -- model selects between predefined paths based on input classification
3. **Add tool selection** -- model chooses from bounded tool set per step
4. **Add planning** -- model creates action plans with human approval before execution
5. **Full autonomy** -- only for low-risk, well-scoped, proven tasks with comprehensive monitoring

Increase autonomy incrementally as confidence grows. Never skip steps. Each level requires its own evaluation suite.

---

## Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| **Over-autonomy** | Agent takes irreversible actions without confirmation | Add human-in-the-loop gates for high-risk actions |
| **Tool overload** | 50+ tools confuse LLM selection | Curate to minimum needed; group related tools |
| **Implicit state** | Relying on LLM memory instead of explicit tracking | Use structured state objects |
| **No termination conditions** | Unbounded loops burning tokens and time | Set max iterations, token budgets, timeout |
| **Monolithic agents** | One agent doing everything | Decompose into specialized agents or workflow stages |
| **Missing error handling** | Assuming tools always succeed | Implement retry, fallback, graceful degradation |
| **No observability** | Deploying without logging | Log everything, assign trace IDs, build dashboards |
| **Premature optimization** | Over-engineering before proving the approach works | Start simple, measure, add complexity when data justifies it |
