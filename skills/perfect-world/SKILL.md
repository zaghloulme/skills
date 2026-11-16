---
name: perfect-world
description: The "perfect world" doctrine for designing and refactoring code so every rule is enforced at the layer that cannot forget it. Use whenever fixing audit findings, designing auth, permissions, rate limiting, or data invariants, planning refactors, hardening security, or when the user says "perfect world", "maintainable", "small blocks", "best practice", or asks how a rule should be enforced. Also use proactively when you notice a rule living in a comment, a convention, or duplicated handler checks.
---

# Perfect World

Every rule is enforced at the layer that cannot forget it. Almost every real
defect has the same shape: a correct rule existed, but its enforcement point
was optional, duplicated, or influenced by the thing it defends against — an
optional parameter someone forgets to pass, a permission check hand-called in
one handler but not its sibling, a check-then-insert with no constraint behind
it, a secret logged by hand at each call site. When designing or fixing a rule,
do not add a reminder — move the enforcement to a place where forgetting is
impossible.

Maintainability, operationally: **small blocks that get the job done, easy to
read, one meaning living in exactly one place.** If a rule is written twice
(say, in the docs and in three handlers), the code does not have the rule —
it has copies, and copies drift. Consolidate before you extend.

## The enforcement ladder

Place each rule at the highest layer that can hold it. Work down only when the
layer above genuinely cannot express the rule.

1. **Schema constraint** — unique/partial unique indexes, CHECKs, FKs,
   conditional `INSERT … SELECT … WHERE` for capacity-style invariants. The
   database refuses the bad state even under concurrency; handlers just map
   constraint errors to domain codes.
2. **Route metadata** — authorization, audience, and rate limits declared on
   the route definition, enforced by one middleware. A route with no declared
   permission fails a startup assertion, not a code review.
3. **Platform primitive** — things the runtime or provider enforces:
   managed rate-limit bindings, HttpOnly/Secure cookie flags, platform secret
   stores (never plain env vars), storage lifecycle rules.
4. **Generator-owned artifact** — migrations, API specs, generated clients:
   produced by the generator from source, freshness-gated in CI, never
   hand-edited.
5. **Single chokepoint** — when code must hold the rule, one small function is
   the only door: the session helper that hashes tokens, the audit helper that
   returns fingerprints, the failure recorder that reads the client IP from
   the request itself. The parameter that can be forgotten does not exist.
6. **Gate (lint/CI/test)** — when nothing above can express it: a completeness
   check (every migration file registered in the journal), a contract test
   (every documented invariant has a test that violates it and expects the
   constraint error), a spec-freshness diff.
7. **Handler code** — last resort. If a rule lives here, it is one edit away
   from being forgotten; say so in a comment and plan its move up the ladder.

## The slice workflow

Ship doctrine as small, complete slices — each one independently reviewable
and green:

1. **Smallest fix** that removes the hole; name the root cause, not just the
   symptom (a role-blind resolver gets a predicate today and a typed
   credentials table tomorrow — say both).
2. **Regression test that reproduces the ORIGINAL bug** — the exact exploit
   or failure, end-to-end where possible (the request an attacker would send,
   the crash the cron would hit). A test that would not have caught the bug is
   not a regression test.
3. **Contracts and docs in the same change** — wire descriptions, reference
   docs, changelog. A rule the docs describe wrongly is a bug in the docs.
4. **All gates green** before touching the next thing. Never stack unverified
   slices.

## Worked patterns

- **Separate doors are structural, not filtered.** When two audiences
  authenticate differently (members by identifier, staff by email + password),
  the credential types live in different rows/tables and each door queries its
  own type — cross-impersonation is unrepresentable, not merely filtered out.
- **Credentials are never stored or logged raw.** Tokens hashed at rest
  (SHA-256 storage key, lookups hash before matching), audit logs carry
  fingerprints, backups encrypted with a fail-loud key. A database dump or a
  log view must never yield a usable secret.
- **Limits key on state the attacker cannot mint.** Client-held cookies are
  UX; the security boundary is a hash of the credential or the platform IP,
  durable in the database. An optional `ip?: string` parameter with a
  security-critical default of `undefined` is itself the bug — the chokepoint
  reads the request.
- **One label, one meaning.** A flag like `banned` has one home module: what
  it blocks (program acceptance), what it never touches (sign-in,
  registration), who may set it (permission), and what it requires (a reason).
  Every consumer imports the rule; no consumer re-implements it.
- **Schema-owned invariants.** Apply-once = partial unique index + map the
  constraint error. Capacity = conditional insert. Multi-row writes = one
  atomic batch, children deleted before parents when FKs restrict.
- **Secrets fail loud.** A missing encryption key aborts the backup; a missing
  mailer credential aborts delivery. Silence is the one unacceptable behavior
  for a security control.

## Anti-patterns (refuse these)

- A rule enforced by comment, convention, or "the other handler does it too".
- Optional parameters whose default silently disables a security control.
- Check-then-act across rows with no constraint or lock behind it.
- Client-held state (cookie, header, hidden field) as the key for a limit the
  client has stake in defeating.
- Two sources of truth for one meaning (a doc count, a duplicated schema, a
  hand-copied contract) — consolidate first, then change.
- Hand-edited generated artifacts, and hand-written migrations.
