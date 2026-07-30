---
name: desktop-pet-builder
description: Build, repair, animate, quality-check, and package a Windows desktop-pet EXE from a user-supplied character image. Use when creating or improving a transparent, frameless, always-on-top PySide6 desktop companion; adding mouse interaction, context menus, chat bubbles, walking, sleeping, feeding, follow-mouse behavior, animation comfort fixes, or PyInstaller delivery.
---

# Desktop Pet Builder

Create a calm, responsive Windows desktop pet while preserving the supplied character identity. Use PySide6, never Tkinter, and deliver a directly runnable EXE without overwriting a running release.

## Workflow

1. Inspect the project and existing process state before changing files. Preserve user artwork, old releases, shortcuts, and unrelated changes. Check Python and the project virtual environment first; install dependencies only if the user authorized it.
2. Read `references/production-playbook.md`. If new character art or motion frames are needed, read the installed `$imagegen` instructions and use the supplied image as an identity reference. Do not claim exact facial preservation without visual QA.
3. Build the PySide6 shell and behavior state machine. Use the interaction contract in the reference. A follow mode must always have at least two discoverable exit paths, including global `Esc`.
4. Prepare transparent assets and animation frames. Run `scripts/check_animation_frames.py` before packaging whenever a frame set changes. Resolve baseline or bounding-box warnings before relying on timing tricks.
5. Apply the comfort defaults: discrete fixed-duration frame holds, no photo cross-fade, no stacked procedural wobble on top of animated walking, subtle effects only, and calm idle behavior. See `references/animation-comfort.md` for the required limits.
6. Verify source syntax, launch the application, exercise each menu state, test follow exit, and check that the exact test process is stopped afterward. Package with PyInstaller using explicit data inclusions for assets and frames.
7. Copy the build to a new, descriptive release filename, hash it, and create or update a shortcut only after checking that its target is not running. Report the EXE path, behavior changes, verification performed, and recovery path.

## Required product contract

- Transparent, borderless `Qt.Tool` window; no taskbar clutter; optional always-on-top state.
- Left drag moves the pet. Wheel adjusts scale while retaining its visual center.
- Left click cycles restrained interactions such as a small jump, head-pat response, conversation, and gentle squash. Do not make rapid shake or squash the normal idle behavior.
- Right-click menu includes chat, head pat, feed, walk, sleep, follow mouse, size, topmost, return-to-corner, and exit.
- Place short Chinese bubbles above or beside the character without obscuring the face or body. Use bounded display times and avoid attention-grabbing typewriter/particle effects by default.
- Follow mouse must be stoppable through `Esc`, clicking the pet, and an explicit checked menu item labeled “停止跟随鼠标（Esc）”.
- Use one stable identity per animation family. Do not mix generated frames whose face, clothing, scale, or viewpoint drift.

## Animation decision rules

- Prefer 4–8 coherent pose frames per action over continuous transforms of one still image.
- Treat each action strip as its own source of motion: do not add bobbing, rotation, scale pulse, dust, or sparkles merely to make it appear active.
- Hold each frame discretely for a fixed duration. Do not blend neighbouring photographic frames; alpha blending creates double facial features and perceived frame-rate fluctuation.
- Keep idle slower than active states. Use a small, infrequent blink; do not combine a drawn blink with an already-blinking idle strip.
- When the user reports dizziness, eyestrain, “too exaggerated”, “hard”, or “frames keep changing”, first disable cross-fades and compounded transforms, then reduce amplitude and particle frequency. Do not respond by increasing FPS or adding more effects.

## Packaging safeguards

- Include every runtime image directory in the `.spec` file. Test the packaged EXE, not only `python main.py`.
- Never overwrite a running EXE. Use a versioned release name and leave previous releases recoverable.
- Before terminating anything, match both process name and full executable path. Stop only the process launched for the test or the exact old release the user asked to close.
- Use `py_compile`, a headless or offscreen smoke test when possible, then a short real Windows launch test. Record SHA-256 for the delivered EXE.

## Resources

- Read `references/production-playbook.md` for the end-to-end implementation and QA checklist.
- Read `references/animation-comfort.md` when designing, diagnosing, or repairing frame motion.
- Run `scripts/check_animation_frames.py <frames-dir>` after extracting or replacing frame PNGs. It is read-only and reports canvas, baseline, and size consistency.
