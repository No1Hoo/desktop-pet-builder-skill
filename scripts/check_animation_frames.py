#!/usr/bin/env python3
"""Read-only PNG frame registration audit for desktop-pet animation directories."""
from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image


def alpha_bbox(path: Path) -> tuple[int, int, int, int] | None:
    with Image.open(path) as image:
        return image.convert("RGBA").getchannel("A").getbbox()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PNG frame canvases and transparent-alpha registration.")
    parser.add_argument("frames_dir", type=Path)
    parser.add_argument("--max-width-variance", type=int, default=0, help="Pixels; 0 uses 25%% of canvas width.")
    parser.add_argument("--max-height-variance", type=int, default=0, help="Pixels; 0 uses 20%% of canvas height.")
    parser.add_argument("--max-baseline-variance", type=int, default=4)
    args = parser.parse_args()
    files = sorted(args.frames_dir.glob("*.png"))
    if not files:
        print(f"ERROR: no PNG frames found in {args.frames_dir}")
        return 2
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        groups[path.stem.rsplit("_", 1)[0]].append(path)
    failed = False
    for action, paths in sorted(groups.items()):
        canvases: set[tuple[int, int]] = set()
        boxes: list[tuple[Path, tuple[int, int, int, int]]] = []
        for path in paths:
            with Image.open(path) as image:
                canvases.add(image.size)
            box = alpha_bbox(path)
            if box is None:
                print(f"FAIL {action}: {path.name} is fully transparent")
                failed = True
            else:
                boxes.append((path, box))
        if len(canvases) != 1:
            print(f"FAIL {action}: inconsistent canvas sizes: {sorted(canvases)}")
            failed = True
            continue
        widths = [box[2] - box[0] for _, box in boxes]
        heights = [box[3] - box[1] for _, box in boxes]
        baselines = [box[3] for _, box in boxes]
        width_span = max(widths) - min(widths)
        height_span = max(heights) - min(heights)
        baseline_span = max(baselines) - min(baselines)
        canvas_width, canvas_height = next(iter(canvases))
        width_limit = args.max_width_variance or round(canvas_width * 0.25)
        height_limit = args.max_height_variance or round(canvas_height * 0.20)
        status = "PASS"
        if width_span > width_limit or height_span > height_limit or baseline_span > args.max_baseline_variance:
            status = "WARN"
            failed = True
        print(f"{status} {action}: frames={len(paths)} canvas={next(iter(canvases))} bbox-width-span={width_span}px/{width_limit}px bbox-height-span={height_span}px/{height_limit}px baseline-span={baseline_span}px/{args.max_baseline_variance}px median-baseline={statistics.median(baselines):.1f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
