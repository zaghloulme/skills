---
name: walkthrough
description: Walk through a real user's task to critique, compare, or improve product UX. Use for confusing flows, visual hierarchy, design comparisons, and verifying a redesign across relevant states and devices.
---

# Walkthrough

## Frame the job

Honor the requested mode. A critique ends with evidence and recommendations. A comparison evaluates both versions against the same task and acknowledges what the earlier design did better. An implementation ends with the changed flow replayed. Use the design or development surface the user chose and respect its editing scope.

Identify the actor, permissions, normal entry point, device, representative record, decision and end state. Read existing product terminology and design conventions. Ask only when the missing answer changes the work. Define success in observable terms before editing. Include one adjacent behavior likely to regress. Keep the criteria stable across attempts. Record any user-directed scope change.

## Establish a baseline

Use the available surface. In a working product, start from the normal entry point and act through visible controls using a browser or the existing automation runner. Observe the result as well as the click. In a prototype, distinguish wired transitions from simulated state. With static frames, ground visual findings in identifiable details and specify how an interaction claim could be checked. With a new flow, use its specified job and constraints as the baseline.

For live systems verify tenant, role, environment and side effects before interacting. A staging label alone cannot establish that outgoing email, payments or webhooks are isolated. Use fixtures and isolated integrations for consequential replays. If isolation or authorization is unclear, stop before the side effect and continue the safe portion. Keep secrets, real customer details and sensitive traces out of shared artifacts. Release only within the user's authorization.

## Find the design decision

Trace what the user must notice, interpret, decide, do and confirm. Inspect the point of greatest friction first. Give each finding a location, a visible or reproducible observation, the consequence for the task, and a way to verify the proposed change.

- For orientation, compare page identity with navigation, selected state and back path.
- For scope, inspect which records a filter or action appears to affect. Try changing it and observe which records actually change.
- For hierarchy, compare what attracts attention with what the person needs for their next decision. Check content, grouping, alignment, contrast and spacing before adjusting decoration.
- For recognition, check labels, affordances, history and nearby context. Use the team's domain terms. Distinguish different business states that share the same label.
- For feedback, inspect pending, success, failure and recovery where relevant. Check keyboard focus, narrow layouts, long or translated labels, permissions and realistic volumes when affected.
- Preserve strengths of the baseline. Identify credible trade-offs. Treat predictions about user preference as hypotheses until observed with users.

When a term could mean two different things, trace one real example of each meaning. Identify who acts next and what changes in the product. Check the existing workflow and terminology. Ask a focused question only if the distinction still changes the design.

When two designs remain plausible, name the decision they handle differently. Walk the same actor through each with the same data and starting state. Compare what they can see, decide and do at the disputed step. Recommend the option that best meets the task criteria and state the trade-off.

## Improve and replay

For implementation, change one coherent cause at a time using the project's components. Replay the original task with equivalent state and data. Inspect the rendered result, run relevant existing checks, and exercise the adjacent behavior. Keep the change if it meets its intended criterion without introducing a material regression. Otherwise revise or undo only your own change. After repeated misses, revisit the diagnosis. Avoid repeating a failed approach without new evidence.

Keep the active task, acceptance checks, latest replay results and open issues in the current session’s working context. Return findings and evidence pointers in the requested response. Ordinary reviews and implementation runs create zero persistent walkthrough documents. This includes plans, checklists, iteration logs and summaries in any format.

When the user requests a saved report or a project rule requires one, update the designated document in place. If a new report is requested, use one document for the whole run unless the request specifies multiple deliverables. Reuse existing test output and trace links. Put temporary captures in the runner's artifact location or a task-scoped temporary directory outside the source tree.

Before finishing, check changed and untracked paths against the starting state where file access permits. Remove only disposable files you can attribute to this run. Preserve user files, requested deliverables and project-required evidence.

## Close on evidence

For every material acceptance check report pass, fail or unverified, with the evidence and tested surface. For implementation, replay after the last relevant edit. Identify the actual tested build, including uncommitted changes when applicable. Reuse an existing release runner when available so its results can be checked independently. Record a failed or skipped check honestly. Keep working on failed checks while an authorized and meaningful attempt remains. When blocked, report the precise missing evidence or decision and finish independent checks.

For a review, prioritize findings by task impact. For a comparison, identify improvements, regressions and uncertain effects. For implementation, give the outcome, final replay evidence, trade-offs and outstanding gaps. Keep the report proportional to the task.

Example: In a document list, moving sort into the toolbar can clarify which records it affects while removing its icon can make sorting harder to discover. A screenshot supports both visual observations. A working replay can establish whether the order changes and keyboard focus is preserved. Evidence from representative users is needed to claim they found it faster.
