from __future__ import annotations

from pathlib import Path

from PIL import Image


def trim(path: Path, padding: int = 10) -> None:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.point(lambda value: 255 if value > 10 else 0).getbbox()
    if bbox is None:
        raise RuntimeError(f"{path} has no visible pixels")
    left, top, right, bottom = bbox
    crop = image.crop(
        (
            max(0, left - padding),
            max(0, top - padding),
            min(image.width, right + padding),
            min(image.height, bottom + padding),
        )
    )
    crop.save(path, optimize=True)
    print(f"{path.name}: {image.size} -> {crop.size}")


if __name__ == "__main__":
    asset_dir = Path(__file__).resolve().parent / "assets"
    for filename in ("chat.png", "pat.png", "feed.png", "sleep.png", "walk.png"):
        trim(asset_dir / filename)
