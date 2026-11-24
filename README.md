# Skills

My agent skills — writing, reasoning, design and engineering discipline I use every day, plus the odd bit of personal automation. Straight from my `.agents` directory.

Small, self-contained, and composable. They work with any model and any agent that reads `SKILL.md`.

[![skills.sh](https://skills.sh/b/zaghloulme/skills)](https://skills.sh/zaghloulme/skills)

## Installation

```bash
# Install everything (pick your agent when prompted)
npx skills@latest add zaghloulme/skills

# Or target specific agents and skills, non-interactively
npx skills@latest add zaghloulme/skills -a claude-code -a cursor -a codex -y

# Install a single skill
npx skills@latest add zaghloulme/skills --skill perfect-world

# List what's available without installing
npx skills@latest add zaghloulme/skills --list
```

To update later, run `npx skills@latest update`.

## What's here

### Writing & reasoning

| Skill | What it does |
| --- | --- |
| [`ijaz`](skills/ijaz/SKILL.md) | Strengthen writing through precise thought, expressive wording and concise form. Speak less to say more. |
| [`millionfold`](skills/millionfold/SKILL.md) | Enforced long-horizon reasoning protocol. Extracts every assumption, calculates ceilings, mandates redesign when warranted, and audits output through an adversarial sub-agent. |
| [`millionfold-evolved`](skills/millionfold-evolved/SKILL.md) | Millionfold Protocol v2 — evolved by GEPA over 30 generations of real evolutionary optimisation. |

### Engineering

| Skill | What it does |
| --- | --- |
| [`perfect-world`](skills/perfect-world/SKILL.md) | The "perfect world" doctrine: design and refactor so every rule is enforced at the layer that cannot forget it — schema constraints, route metadata, single chokepoints — instead of in a comment or a duplicated handler check. |
| [`ai-engineering-guide`](skills/ai-engineering-guide/SKILL.md) | Guidelines for building AI agents, AI apps and LLM-powered systems: agent architecture, prompt engineering, RAG, security hardening, evaluation, model selection and orchestration. |

### Craft

| Skill | What it does |
| --- | --- |
| [`walkthrough`](skills/walkthrough/SKILL.md) | Review or improve a user flow by replaying a realistic task and verifying the outcome. |
| [`dithered-visuals`](skills/dithered-visuals/SKILL.md) | Generate composition-ready imagery and transform it into restrained two-color Bayer 4×4 dither artwork. |

## Repository layout

```
skills/
  <name>/
    SKILL.md          # required — front matter (name, description) + instructions
    ...               # optional references, scripts, assets
```

Skills live under `skills/<name>/`, the layout `npx skills` discovers automatically.

## Licence

Everything here is [MIT](LICENSE), except `millionfold` and `millionfold-evolved`, which are proprietary — their front matter declares `license: Proprietary`. Each skill's own `SKILL.md` is authoritative.
