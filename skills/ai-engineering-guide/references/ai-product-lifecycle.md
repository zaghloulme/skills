# AI Product Lifecycle -- Deep Reference

> Cross-references: `prompt-engineering.md`, `evaluation-and-testing.md`, `model-selection.md`, `security-and-hardening.md`, `rag-and-grounding.md`, `orchestration-patterns.md`

---

## Five Stages

### Stage 1: Ideation
- Identify the business problem, target users, and measurable outcomes
- Define success criteria upfront -- what does "working" look like in quantifiable terms?
- Assess LLM suitability: Does this task require natural language understanding/generation? Is 100% accuracy required (if so, LLM alone is insufficient)?
- Estimate projected value: time savings, error reduction, throughput gains

**Decision Framework -- Is LLM the Right Tool?**

| Signal | Direction |
|--------|-----------|
| Requires natural language understanding or generation | LLM |
| Deterministic with clear rules (tax calculation, routing) | Traditional code |
| 95%+ accuracy required, zero error tolerance | Hybrid: LLM + validation layer |
| Requires real-time proprietary data | RAG + LLM (see `rag-and-grounding.md`) |
| Creative, open-ended, or reasoning-heavy | LLM with chain-of-thought |
| Task involves structured data transforms only | ETL / SQL / rules engine |
| High-volume, latency-sensitive, simple classification | Fine-tuned small model or ML classifier |

**Suitability Exclusions** -- tasks where LLMs add risk without benefit:
- Deterministic business logic (pricing rules, regulatory formulas)
- Real-time financial calculations requiring auditability
- Tasks where the cost of a wrong answer exceeds the value of automation

### Stage 2: Feasibility & Scoping
- **Suitability check**: Is the output deterministic or probabilistic? Can users tolerate variability?
- **Grounding data audit**: Is the necessary knowledge available? In what format? How fresh does it need to be? What is the maintenance burden?
- **Hallucination risk assessment**: What is the cost of a wrong answer in this domain? Map risk: low (internal suggestions), medium (customer-facing info), high (legal, medical, financial)
- **Cost-benefit analysis**: Token costs at projected volume vs. business value delivered. Include prompt engineering effort, infrastructure, ongoing maintenance
- **Technical feasibility**: Required integrations, data pipelines, infrastructure, team skills
- **Ethical review**: Does this use case raise bias, fairness, or transparency concerns? Who is affected by errors?

**Go/No-Go Checklist:**

| Question | Required for Go |
|----------|----------------|
| Is the business value quantifiable? | Yes |
| Is grounding data available and accessible? | Yes (for RAG use cases) |
| Is hallucination risk acceptable for this domain? | Yes |
| Does the team have required skills or can acquire them? | Yes |
| Is the cost-benefit ratio positive at projected scale? | Yes |
| Have ethical/bias concerns been assessed? | Yes |

### Stage 3: Prototyping / PoC
- Rapid experimentation with models and prompts using playground or SDK
- Test with real (or realistic) data, not toy examples
- Establish baseline metrics early (see `evaluation-and-testing.md`)
- Compare 2-3 approaches before committing (e.g., RAG vs. fine-tuning vs. long-context)
- Involve end-users for early feedback -- what they find useful vs. what they distrust
- Goal: Prove the approach works, not build production infrastructure

**Prototype Exit Criteria:**
- Core task achievable with acceptable accuracy on 50+ test cases
- Latency within acceptable range for the use case
- Cost per request sustainable at projected volume
- At least one model-prompt combination meets baseline thresholds
- End-user feedback indicates value (not just novelty)

### Stage 4: Productization
- Full development: UI, data pipelines, security, integration with enterprise systems
- Prompt engineering refinement using iterative methodology (see `prompt-engineering.md`)
- RAG pipeline build-out if applicable (see `rag-and-grounding.md`)
- Security hardening across all 7 defense layers (see `security-and-hardening.md`)
- Testing suite development: unit, integration, regression, adversarial (see `evaluation-and-testing.md`)
- Monitoring and observability infrastructure
- Documentation and runbooks for operations
- Orchestration pipeline configuration (see `orchestration-patterns.md`)

**Productization Checklist:**

- [ ] Prompt templates finalized, version-controlled, and regression-tested
- [ ] Model selection validated via empirical benchmarking (see `model-selection.md`)
- [ ] Input validation and output validation implemented
- [ ] Content filtering configured (input + output)
- [ ] Data masking for PII implemented if applicable
- [ ] Fallback models tested and configured
- [ ] Rate limiting and cost controls in place
- [ ] Monitoring dashboards and alerting configured
- [ ] Runbooks for common failure modes documented
- [ ] Red teaming completed with findings addressed

### Stage 5: Deployment & Monitoring
- **Gradual rollout**: shadow mode (run silently, compare to current) -> canary (small % of traffic) -> staged rollout -> full deployment
- **Performance monitoring**: latency (P50/P90/P99), throughput, error rates, costs per request
- **Quality monitoring**: accuracy metrics, user feedback (thumbs up/down, star ratings), groundedness scores
- **Cost tracking**: actual token consumption vs. budget, cost per request trending
- **Alerting**: metric deviations beyond thresholds, error rate spikes, latency regressions

**Rollout Stage Gates:**

| Stage | Entry Criteria | Duration |
|-------|---------------|----------|
| Shadow | Passes all automated tests | 1-2 weeks |
| Canary (5%) | Shadow metrics match or exceed baseline | 1 week |
| Staged (25% -> 50%) | Canary metrics stable, no critical issues | 1-2 weeks each |
| Full | All staged metrics within thresholds | Ongoing |

---

## Continuous Maintenance

### Model Management
- Track model versions in production with clear version pinning
- Test new versions before upgrading: run full evaluation suite, compare against current baseline
- Monitor provider deprecation notices and plan migrations with buffer time
- Maintain tested fallback models for every critical use case
- Budget 1-2 sprints per year for model migration and re-evaluation

### Prompt Maintenance
- Re-evaluate prompts when models update -- new model versions can shift behavior
- A/B test prompt changes before full deployment
- Version control all production prompts (prompts are code)
- Periodic prompt optimization: reduce token usage, improve quality
- Track prompt performance metrics over time for drift detection

### Knowledge Base Maintenance (RAG)
- Define update cadence aligned with source data freshness (real-time, daily, weekly)
- Monitor for stale or contradictory documents
- Re-embed when embedding models improve or change
- Track retrieval quality metrics over time (precision, recall, relevance scores)
- Prune outdated documents to prevent retrieval noise

### Ongoing Quality Assurance
- Regression testing on every change (prompt, model, data, configuration)
- Red teaming on a regular schedule (monthly for high-risk, quarterly for low-risk)
- User feedback analysis: aggregate patterns, identify systemic issues
- Data drift detection: are real-world inputs diverging from test data?
- Periodic expert review of output quality by domain specialists
- Error categorization dashboard: hallucination rate, format failures, jailbreak attempts

### Sunset Planning
- Define criteria for when to retire or replace an AI feature
- Monitor usage trends -- declining usage may indicate low value or better alternatives
- Plan migration path for dependent systems
- Archive prompts, evaluation datasets, and configuration for institutional knowledge

---

## Team Structure & Roles

| Role | Responsibility |
|------|---------------|
| Product Manager | Business problem definition, success criteria, stakeholder alignment, roadmap |
| AI/ML Engineer | Model selection, prompt engineering, RAG pipeline, evaluation, orchestration |
| UX Designer | User interaction design, feedback mechanisms, trust-building UI patterns |
| Data Engineer | Data pipelines, knowledge base ingestion, embedding infrastructure |
| Security Engineer | Threat modeling, red teaming, compliance, data masking configuration |
| Domain Expert | Ground truth creation, output quality review, edge case identification |
| DevOps/MLOps | Deployment, monitoring, alerting, CI/CD for prompts and configurations |

For smaller teams, roles overlap -- but the responsibilities still need coverage. At minimum: someone owns the business problem, someone owns the technical implementation, someone validates output quality.

---

## Governance & Compliance

### Access Control
Define roles with clear permissions:
- **Admin**: Full configuration access, model deployment, security settings
- **Prompt Engineer**: Prompt CRUD, evaluation execution, A/B testing
- **Experimenter**: Playground access, prototype testing, read-only production
- **Viewer**: Dashboard access, report generation

### Audit Trail
- Log all LLM interactions: input, output, model, version, timestamp, user
- Log all configuration changes: who changed what, when, previous value
- Retention policy aligned with compliance requirements (GDPR: data minimization; regulated industries: longer retention)

### Regulatory Considerations
- **GDPR / CCPA**: Ensure PII is masked before LLM processing; honor data deletion requests; document data flows
- **Industry-specific**: Healthcare (HIPAA), finance (SOX, PCI-DSS), legal (attorney-client privilege boundaries)
- **AI-specific regulation**: EU AI Act risk classification (unacceptable, high, limited, minimal risk); document AI system capabilities and limitations
- **Transparency obligations**: Disclose AI involvement to end users; provide human escalation paths

### Responsible AI Principles
1. **Relevant**: AI outputs must be anchored in factual, contextual data -- not speculation
2. **Reliable**: Systems must be tested, monitored, and maintainable with clear fallbacks
3. **Responsible**: Consider bias, fairness, transparency, and privacy at every design decision. Test for demographic bias. Provide feedback mechanisms. Maintain human oversight for consequential decisions

---

## Key Principles Across All Stages

1. **Start simple**: Begin with the simplest approach that could work. Add complexity only when measurement shows it is needed.
2. **Measure first**: Establish baselines before optimizing. You cannot improve what you do not measure.
3. **Iterate fast in prototyping, slow in production**: Rapid experimentation early; rigorous testing before deployment.
4. **Design for failure**: LLMs are probabilistic. Every output path needs validation and fallback.
5. **Budget for maintenance**: AI systems require ongoing care -- models update, data drifts, prompts degrade. Plan for it from day one.
6. **Human oversight**: For any action with real-world consequences, maintain a human approval step until the system proves reliable at scale.
7. **Responsible AI by default**: Bias testing, transparency, and privacy are not optional add-ons -- they are design requirements.
8. **Cross-functional ownership**: AI products fail when treated as pure engineering projects. Business, UX, domain expertise, and security must be at the table throughout.
