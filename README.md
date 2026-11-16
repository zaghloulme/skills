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

### Craft & automation

| Skill | What it does |
| --- | --- |
| [`dithered-visuals`](skills/dithered-visuals/SKILL.md) | Generate composition-ready imagery and transform it into restrained two-color Bayer 4×4 dither artwork. |
| [`agent-desktop`](skills/agent-desktop/SKILL.md) | Drive a GUI desktop box — open browsers carrying shared logins, watch the screen, click and type like a human. |
| [`thermal-daily-todos`](skills/thermal-daily-todos/SKILL.md) | Compile a daily work plan from your tasks, categorise it cleanly, and print it to a 72 mm thermal printer via ESC/POS. |

## Repository layout

```
skills/
  <name>/
    SKILL.md          # required — front matter (name, description) + instructions
    ...               # optional references, scripts, assets
```

Skills live under `skills/<name>/`, the layout `npx skills` discovers automatically.

## Licence

Each skill is licensed as declared in its own front matter. Unless stated otherwise, everything here is MIT.
