# PySide6 desktop-pet production playbook

## 1. Scope and identity

Start with the supplied character image as the source of truth. Preserve its recognizable face, hairstyle, accessories, colour palette and costume unless the user approves a redesign. Keep the original untouched. Keep generated pose strips separate from source art and only accept a frame family after reviewing it at the intended desktop size.

For image generation, use the installed image-generation skill, attach the original reference, and ask for one coherent action strip with a flat removable background. Ask for complete separated full-body poses, a stable camera/viewpoint, a shared foot baseline, no text, no scenery, no detached glow, no motion streaks, and no cropped limbs. Generate a small repair set for a single failing action rather than rebuilding all states.

## 2. Environment and project setup

1. Detect installed Python versions and existing project virtual environment.
2. Use a project-local virtual environment. Install `PySide6`, `Pillow`, and `PyInstaller` only when absent and within user authorization.
3. Use UTF-8 source files and PowerShell 7 on Windows. Before PowerShell diagnostics, explicitly set console input/output encoding and `chcp 65001`.
4. Create separate directories for `assets/`, `assets/frames/`, `qa/`, `build/`, `dist/`, and final `output/` releases.
5. Do not use Tkinter. Use `QApplication`, `QWidget`, `QPainter`, `QTimer`, `QMenu`, and `QInputDialog` as needed.

## 3. Window shell

Use a frameless `Qt.Tool` widget with `FramelessWindowHint`, `NoDropShadowWindowHint`, and optional `WindowStaysOnTopHint`. Enable a translucent background and paint only the character, bubble, and minimal attached effects. Resize according to a bounded scale factor and clamp window movement to the available screen geometry.

Use a regular timer near 20 ms only to drive input/movement and repaint cadence. That render cadence is not the animation cadence: pose changes must be quantized by the stable duration of their action frame.

## 4. State model

Keep a small explicit state set: `idle`, `chat`, `pat`, `feed`, `walk`, `sleep`, `follow`, `wander`, `drag_run`, `glide`, `jump`, `squash`, `shake`, and `notice`. Store `state_started`, optional `state_duration`, facing direction, drag velocity, energy, affection, bubble expiry, and follow state. One `activate(state, duration=None)` function should reset the action clock and prevent old state timing from leaking into the next interaction.

Map visual actions rather than treating every behavior as a separate image requirement:

| Behavior | Suggested visual action | Notes |
| --- | --- | --- |
| idle / notice | idle | Slow blink only; no continuous breathing transform if the strip already moves. |
| walk / follow / wander / drag | walk | Flip one consistent side-view family for direction; do not swap unrelated side images every frame. |
| chat | wave | Use a restrained wave or attentive pose. |
| pat | pat | One small attached heart is enough. |
| feed | feed | One food prop and a slow bite sequence. |
| sleep | sleep | Slow pose loop; one low-frequency sleep mark at most. |

## 5. Interaction details

### Drag and release

On left press, store global mouse position and original window position. On move past a small threshold, move the widget, update facing from horizontal drag direction, and compute damped velocity. On release, use a limited glide only when velocity crosses a threshold; otherwise return to idle. Clamp all positions. Avoid dust trails during ordinary dragging or walking.

### Click and menu

If the release is not a drag, cycle a short, predictable set of interactions. Keep jump height, squash and shake within the comfort limits. The context menu must make every active mode reversible. `跟随鼠标` becomes a checkable `停止跟随鼠标（Esc）` item when active; `Esc` is polled globally on Windows and the next left click also stops follow.

### Chat and bubbles

Use a short Chinese reply selection with a modest-duration bubble. For real text input, display a `QInputDialog`; cancel must return the pet to idle. Render bubbles in the reserved top portion of the widget, above the head, wrapping text and clipping to the bubble bounds. Do not cover the character.

## 6. Animation assets

Use RGBA PNGs with a shared canvas. After background removal, normalize every action to the same output canvas and a common foot baseline. Preserve transparent margins deliberately so head/hand actions do not get clipped. Track the visual bounding box of each frame; large changes are almost always a source-art or extraction defect, not an animation problem to hide with transforms.

Use `scripts/check_animation_frames.py` for a first consistency pass. Then inspect a contact sheet on a neutral background at normal desktop scale. Verify character identity, frame order, ground contact, no duplicated limbs, no phantom background pixels, and no sudden crop/size jump.

## 7. Comfort-first motion rules

Read `animation-comfort.md` before tuning timing. The baseline design is discrete frames, stable foot registration, low-amplitude one-shot feedback, no opacity morphing, and no always-on decorative particles. When a user has explicitly requested “more natural movement”, add coherent source frames before adding procedural movement. When a user reports discomfort, remove complexity first.

## 8. Build and delivery

1. Compile: `python -m py_compile main.py`.
2. Run an offscreen smoke test that creates the widget, loads each required sprite family, and confirms frame selection returns one discrete frame rather than a blended pair.
3. Build with `pyinstaller --noconfirm --clean desktop_pet.spec`; ensure `.spec` includes `assets/frames` and every fallback asset.
4. Copy `dist` output to a new user-facing versioned name in the release folder. Do not copy over a running target.
5. Start the packaged EXE briefly, verify the exact process path, then close only that test process. Confirm no child process remains.
6. Compute SHA-256. Create a desktop shortcut only if requested; check its target and never silently repoint an existing shortcut.

## 9. Regression checklist

- Character image loads with transparent background; no white/magenta fringe.
- Window is transparent, borderless, movable, scalable, and topmost state toggles correctly.
- Menu commands invoke chat, pat, feed, walking, sleep, follow, return, resize, topmost and exit.
- Follow stops with `Esc`, left click, and menu command.
- Each action returns to idle after its planned duration; sleep/walk remain toggled until stopped.
- Bubble stays outside the character silhouette and disappears on time.
- Frame holds are fixed; no alpha cross-fade, face ghosting, or simultaneous scale/rotate/bob during a frame loop.
- EXE launches without a Python console or missing resource error.
- Only the intended test process was closed; older releases remain intact.
