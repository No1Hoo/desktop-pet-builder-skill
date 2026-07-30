from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
from PIL import Image


def key_magenta(image: Image.Image) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA")).astype(np.float32)
    red, green, blue = rgba[..., 0], rgba[..., 1], rgba[..., 2]
    magenta_base = np.minimum(red, blue)
    chroma_gap = magenta_base - green
    chroma_strength = np.clip((chroma_gap - 58.0) / 48.0, 0.0, 1.0)
    brightness_strength = np.clip((magenta_base - 135.0) / 58.0, 0.0, 1.0)
    alpha = np.clip(255.0 * (1.0 - chroma_strength * brightness_strength), 0, 255).astype(np.uint8)
    result = Image.fromarray(rgba.astype(np.uint8), "RGBA")
    result.putalpha(Image.fromarray(alpha, "L"))
    return result


def extract(source: Path, action: str, output_dir: Path, frames: int = 4) -> None:
    image = Image.open(source).convert("RGBA")
    cell_width = image.width // frames
    raw_frames: list[Image.Image] = []
    for index in range(frames):
        left = index * cell_width
        right = image.width if index == frames - 1 else (index + 1) * cell_width
        cell = key_magenta(image.crop((left, 0, right, image.height)))
        alpha = cell.getchannel("A")
        bbox = alpha.point(lambda value: 255 if value > 18 else 0).getbbox()
        if bbox is None:
            raise RuntimeError(f"Frame {index} has no foreground")
        pad = 10
        bbox = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(cell.width, bbox[2] + pad),
            min(cell.height, bbox[3] + pad),
        )
        raw_frames.append(cell.crop(bbox))

    max_width = max(frame.width for frame in raw_frames)
    max_height = max(frame.height for frame in raw_frames)
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(raw_frames):
        canvas = Image.new("RGBA", (max_width, max_height), (0, 0, 0, 0))
        canvas.alpha_composite(frame, ((max_width - frame.width) // 2, max_height - frame.height))
        destination = output_dir / f"{action}_{index:02d}.png"
        canvas.save(destination, optimize=True)
        print(destination)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: extract_animation_strip.py SOURCE ACTION OUTPUT_DIR")
    extract(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
