from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def remove_magenta(source: Path, output: Path, padding: int = 12) -> None:
    image = Image.open(source).convert("RGBA")
    pixels = np.asarray(image).astype(np.float32)
    red, green, blue = pixels[..., 0], pixels[..., 1], pixels[..., 2]

    # Generated chroma backgrounds vary from hot pink to deep magenta.
    # This score deliberately keys only pixels whose red AND blue channels
    # strongly dominate green, so warm skin and the yellow flower stay opaque.
    magenta_base = np.minimum(red, blue)
    chroma_gap = magenta_base - green
    chroma_strength = np.clip((chroma_gap - 58.0) / 48.0, 0.0, 1.0)
    brightness_strength = np.clip((magenta_base - 135.0) / 58.0, 0.0, 1.0)
    key_strength = chroma_strength * brightness_strength
    alpha = np.clip(255.0 * (1.0 - key_strength), 0, 255).astype(np.uint8)

    result = Image.fromarray(pixels.astype(np.uint8), "RGBA")
    result.putalpha(Image.fromarray(alpha, "L"))
    visible_bbox = result.getchannel("A").point(lambda value: 255 if value > 18 else 0).getbbox()
    if visible_bbox is None:
        raise RuntimeError(f"No foreground detected in {source}")
    left, top, right, bottom = visible_bbox
    result = result.crop(
        (
            max(0, left - padding),
            max(0, top - padding),
            min(result.width, right + padding),
            min(result.height, bottom + padding),
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output, optimize=True)
    print(f"{source.name} -> {output.name} {result.size}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent / "assets"
    mapping = {
        "chat_raw.png": "chat.png",
        "pet_raw.png": "pat.png",
        "feed_raw.png": "feed.png",
        "sleep_raw.png": "sleep.png",
        "walk_raw.png": "walk.png",
    }
    for source_name, output_name in mapping.items():
        remove_magenta(root / "raw" / source_name, root / output_name)
