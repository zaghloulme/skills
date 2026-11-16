---
name: thermal-daily-todos
description: Compiles a daily work plan from user-provided tasks, categorizes them cleanly, and prints to a 72mm thermal printer via ESC/POS. Use when the user asks for a daily todo list, task breakdown, thermal print, work plan receipt, or wants tasks organized and printed. Asks for clarification when anything is unclear instead of assuming.
---

# Thermal Daily Todos

Print a clean, professional daily work plan to a 72mm thermal printer. Same style as `print_v7.py`: centered title, inverted category bars, `[ ]` checkboxes, calm footer.

## Before doing anything — clarify, don't assume

Ask the user when any of these are unclear:

- **Task list incomplete** — they gave a vague request without listing tasks
- **Printer IP** — default is `10.0.1.111:9100`; confirm if unknown or print fails
- **Breakdown depth** — default is **one line per task they gave**; ask before splitting into subtasks
- **Deadlines** — ask which task is urgent if multiple deadlines exist
- **Categories** — use defaults below unless they want different groupings
- **Extra tasks** — never add tasks the user did not mention

Use `AskQuestion` when available. Otherwise ask conversationally. Wait for answers before writing YAML or printing.

## Task rules

1. **Only user tasks** — include exactly what they listed, lightly edited for brevity
2. **One line per task** — format: `ClientName - short description` (ASCII hyphen, not em dash)
3. **No invented subtasks** — no "screenshot", "brain dump", "sanity check" unless they asked
4. **No strategy essays** — no tier systems, time estimates, or motivational blocks on the receipt
5. **ASCII-safe text** — use `-` not `—`; avoid smart quotes and special Unicode

## Default categories

| Category | Use for |
|----------|---------|
| `TODAY` | Urgent / deadline today or tomorrow |
| `CLIENTS` | Client deliverables |
| `INTERNAL` | Business, naming, research, team setup |
| `ADMIN` | Bills, invoices, subscriptions, personal admin |

Skip empty categories. Ask the user if a task doesn't fit cleanly.

## Workflow

### 1. Gather tasks

Collect the user's task list. If missing or ambiguous, ask before proceeding.

### 2. Write YAML

Create `scripts/daily-todos/YYYY-MM-DD.yaml` next to the print script:

```yaml
date: "Sat 13 Jun 2026"
printer_ip: "10.0.1.111"

categories:
  - name: "TODAY"
    tasks:
      - "Marzone - finish/deploy platform, demo Sun"
  - name: "CLIENTS"
    tasks:
      - "BlackRhino - send shipping/refund Google form"
```

Template: [scripts/daily-todos-template.yaml](scripts/daily-todos-template.yaml)

### 3. Print

Run from the skill's `scripts/` directory:

```bash
python3 ~/.agents/skills/thermal-daily-todos/scripts/print-daily-todos.py
python3 ~/.agents/skills/thermal-daily-todos/scripts/print-daily-todos.py --file daily-todos/2026-06-13.yaml
python3 ~/.agents/skills/thermal-daily-todos/scripts/print-daily-todos.py --ip 10.0.1.176
python3 ~/.agents/skills/thermal-daily-todos/scripts/print-daily-todos.py --save
```

If a project already has `saas/scripts/print-daily-todos.py`, prefer that copy when working in that repo.

On print failure: save with `--save`, report the error, ask user to confirm printer IP.

### 4. Confirm

Tell the user it printed (or saved to `/tmp/daily-todos.bin`). Show the task list in chat if helpful.

## Receipt layout

```
        TODAY
    Sat 13 Jun 2026
========================================

 ███████████ CLIENTS ██████████████████

[ ] BlackRhino - send Google form
[ ] IFT - About + Contact images

----------------------------------------
        one at a time
```

## Project copy

The conjure-ltd project also ships this at `saas/scripts/print-daily-todos.py`. Keep both in sync when fixing encoding or layout bugs.
