---
name: desktop-pet-builder
description: Build, repair, animate, quality-check, and deliver a native Linux desktop pet from a user-supplied character image. Use when creating or improving a transparent, frameless, always-on-top PySide6 desktop companion on Linux; adding mouse interaction, context menus, chat bubbles, walking, sleeping, feeding, follow-mouse behavior, animation comfort fixes, launchers, or desktop integration.
---

# Desktop Pet Builder for Linux

Create a calm, responsive Linux desktop pet while preserving the supplied character identity. Use PySide6, never Tkinter. Keep Linux delivery separate from Windows EXE releases: do not modify or duplicate files under `releases/`, and do not use the Windows `.spec` as the Linux launch path.

## Workflow

1. Inspect the project, desktop session (`XDG_SESSION_TYPE`, `DISPLAY`, `WAYLAND_DISPLAY`) and existing process state before changing files. Preserve user artwork, Windows releases, shortcuts and unrelated changes. Check Python and the project virtual environment first; install dependencies only if the user authorized it.
2. Read `references/production-playbook.md`. If new character art or motion frames are needed, read the installed `$imagegen` instructions and use the supplied image as an identity reference. Do not claim exact facial preservation without visual QA.
3. Build the PySide6 shell and behavior state machine. Use the interaction contract in the reference. A follow mode must always have at least two discoverable exit paths. On Linux, do not add unsafe `ctypes` X11 polling merely to emulate Windows global `Esc`; retain click and menu exits, and support `Esc` while the pet has focus.
4. Prepare transparent assets and animation frames. Run `scripts/check_animation_frames.py` before packaging whenever a frame set changes. Resolve baseline or bounding-box warnings before relying on timing tricks.
5. Apply the comfort defaults: discrete fixed-duration frame holds, no photo cross-fade, no stacked procedural wobble on top of animated walking, subtle effects only, and calm idle behavior. See `references/animation-comfort.md` for the required limits.
6. Verify source syntax, run an offscreen smoke test, then launch in the real Linux desktop session. Exercise each menu state, test follow exits, and stop only the exact test process afterward.
7. Deliver a repository-local launcher plus an optional trusted `.desktop` entry. Keep the virtual environment untracked. Report the launcher path, desktop-session compatibility, behavior changes, verification performed and recovery path.

## Required product contract

- Transparent, borderless `Qt.Tool` window; no taskbar clutter; optional always-on-top state.
- Left drag moves the pet. Wheel adjusts scale while retaining its visual center.
- Left click cycles restrained interactions such as a small jump, head-pat response, conversation, and gentle squash. Do not make rapid shake or squash the normal idle behavior.
- Right-click menu includes chat, head pat, feed, walk, sleep, follow mouse, size, topmost, return-to-corner, and exit.
- Place short Chinese bubbles above or beside the character without obscuring the face or body. Use bounded display times and avoid attention-grabbing typewriter/particle effects by default.
- Follow mouse must be stoppable by clicking the pet and an explicit checked menu item. `Esc` must also work while the pet has keyboard focus; global `Esc` is optional only when implemented safely for the active Linux display server.
- Use one stable identity per animation family. Do not mix generated frames whose face, clothing, scale, or viewpoint drift.

## Animation decision rules

- Prefer 4–8 coherent pose frames per action over continuous transforms of one still image.
- Treat each action strip as its own source of motion: do not add bobbing, rotation, scale pulse, dust, or sparkles merely to make it appear active.
- Hold each frame discretely for a fixed duration. Do not blend neighbouring photographic frames; alpha blending creates double facial features and perceived frame-rate fluctuation.
- Keep idle slower than active states. Use a small, infrequent blink; do not combine a drawn blink with an already-blinking idle strip.
- When the user reports dizziness, eyestrain, “too exaggerated”, “hard”, or “frames keep changing”, first disable cross-fades and compounded transforms, then reduce amplitude and particle frequency. Do not respond by increasing FPS or adding more effects.

## Linux delivery safeguards

- Use a project-local `.venv/` and keep it ignored by Git. Do not install Python packages globally.
- If Qt reports that the `xcb` platform plugin cannot initialize, inspect the exact missing shared library before installing anything. On Ubuntu 24.04 with current PySide6, `libxcb-cursor0` may be required.
- A `.desktop` entry must use absolute `Exec` and `Icon` paths, set `Terminal=false`, be executable, and be marked trusted when the desktop supports that metadata.
- Before terminating anything, match both process name and full script or interpreter path. Stop only the exact process launched for the test.
- Use `py_compile`, the frame checker, an offscreen smoke test and a real X11/Wayland launch. A surviving process alone is insufficient; visually confirm transparency, character rendering and interaction.
- Do not commit generated virtual environments, core dumps, screenshots, build output or Linux package caches.

## Resources

- Read `references/production-playbook.md` for the Linux implementation and QA checklist.
- Read `references/animation-comfort.md` when designing, diagnosing, or repairing frame motion.
- Run `scripts/setup_linux.sh` to create the repository-local virtual environment for the included example.
- Run `启动霞姐桌宠.sh` to launch the included example without a terminal window.
- Run `scripts/check_animation_frames.py <frames-dir>` after extracting or replacing frame PNGs. It is read-only and reports canvas, baseline, and size consistency.
