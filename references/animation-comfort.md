# Animation comfort and stability guide

## Diagnose the report before changing assets

| User report | Likely cause | First correction |
| --- | --- | --- |
| “眼睛不舒服” / “太浮夸” | Too many simultaneous effects, fast shake, large transform amplitude, bright particles | Disable nonessential particles and compounded transforms; reduce one-shot motion. |
| “帧数一直在变” / “脸在变” | Alpha blend between photographic frames, frame canvas mismatch, two animation sources alternating | Use discrete holds, one action strip, common canvas and baseline. |
| “很坚硬” | Only a still image is being translated/scaled, poses do not have true limb changes | Create a coherent 4–8-frame pose set for that action. |
| “不流畅” | Bad frame order, long/uneven cadence, foot baseline drift, skipped source poses | Fix ordering and registration; use uniform holds before raising cadence. |
| “忽大忽小” | Per-frame crop/bounding-box variance or auto-fit dimensions differ | Normalize output canvas and inspect bounding-box variance. |

## Default cadence

Use integer millisecond frame holds rather than render-time fractions. Starting values:

| Action | Hold per frame | Intent |
| --- | ---: | --- |
| idle | 640 ms | Quiet; four-frame loop produces a slow blink. |
| walk | 170 ms | Clear, moderate gait without blur. |
| wave/chat | 240 ms | Legible hand gesture. |
| pat | 280 ms | Warm reaction without twitching. |
| feed | 320 ms | Slow bite/readable prop. |
| sleep | 720 ms | Low stimulation. |

Change cadence only after the source frames pass registration QA. Keep values stable within the same action. Do not alpha blend frame N into N+1 for photographic art; direct switching at a fixed hold is more readable than morphing.

## Motion limits

Apply a procedural transform only if the state lacks a dedicated pose frame and the effect is necessary for feedback. Use one transform at a time.

- Jump: maximum vertical displacement about 10–15% of character display height; no rotation.
- Squash: maximum vertical reduction 12% and horizontal expansion 6%; a single short pulse.
- Shake: horizontal amplitude at most 2% of width, decay within 0.8 s; no rotation.
- Notice: upward offset at most 1% of height.
- Idle, walk, follow, wander, drag, pat, feed, chat, sleep: no extra continuous scale, rotation, or bob when their image sequence already carries motion.

## Effects and bubbles

Default to no detached effects. If user wants feedback, permit at most one small, low-frequency state-relevant element: a heart for pat, food crumb for feed, or sleep mark for sleep. Avoid sparks, dust, speed lines, glows, halos, trails, and rapid typewriter reveals. The bubble is the primary communication surface and must be outside the character silhouette.

## Technical pattern

Use a fixed selection formula:

```python
frame_ms = {"idle": 640, "walk": 170, "wave": 240}
index = int(elapsed_seconds * 1000 // frame_ms[action]) % len(frames)
sprite = frames[index]
```

Draw only `sprite`. Do not calculate `next_index`, opacity, blend factor, or separate walking bob unless the style is deliberately non-photographic and the user has approved it.

## Acceptance test

Watch each loop for at least three cycles at the user’s actual chosen scale. It passes only when the face stays singular, feet have a stable ground line, silhouette does not pulse in size, the intended gesture is readable, and idle does not demand attention from peripheral vision.
