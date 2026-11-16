---
name: agent-desktop
description: Use a GUI desktop box on hpe01 — open browsers carrying shared logins, see the screen via screenshots, click/type/scroll like a human. Use when asked to open or test a site in a browser, do computer-use/GUI work, or when the user says "use your desktop/box".
---

# Agent desktop boxes (hpe01)

One virtual desktop per agent plus a "shared" box. All 1920x1080. Boxes: shared, alpha, beta. Each agent owns ONE box and never touches another's.

## Box map
- shared: display :99 — you watch at http://100.116.20.49:6080/vnc.html
- alpha: display :91 — http://100.116.20.49:6081/vnc.html
- beta: display :92 — http://100.116.20.49:6082/vnc.html

## Browser with shared logins
- `agent-browser-open <box> [url]` — clones the master profile (all shared cookies/logins) into this box's profile, then launches Chromium maximized.
- `agent-browser-close <box>` — kill the box's browser (required before promote).
- `agent-browser-promote <box>` — push the box's profile back to master. Do this after logging into a new site so every box inherits the login on next open.
- Cloning happens at OPEN only (Chromium locks a running profile — no live sync). To pick up everyone's latest logins, close + re-open.

## Computer use (see, then act)
- `agent-use <box> shot [file]` — screenshot, default /tmp/desktop-<box>.png. ALWAYS view the shot after an action; never act blind.
- `agent-use <box> click X Y` — left click at pixel coordinates
- `agent-use <box> type "text"` — type text
- `agent-use <box> key Return|ctrl+l|ctrl+t|F5|Tab` — press keys/shortcuts
- `agent-use <box> scroll up|down`
- `agent-use <box> windows` — list window titles
- `agent-use <box> activate "TitleSubstring"` — focus/raise a window
- `agent-use <box> exec -- xterm` — run any GUI program on the box's display

## Standard flows
- Open + verify: `agent-browser-open alpha https://site` → `shot` → read the image.
- Navigate: key ctrl+l → type URL → key Return → shot.
- New logins: do them on the shared box (user watches 6080), then `agent-browser-close shared && agent-browser-promote shared`.
- Multiple tabs: key ctrl+t, new tab starts focused.

## Rules
1. Screenshot after every step before the next — coordinates come from the last screenshot, top-left is 0,0.
2. Never set DISPLAY manually; tools target boxes by name.
3. Promote sparingly: finish your logins, then promote once.
4. Browser won't start → `agent-browser-close <box>` then re-open (stale profile lock).
