from __future__ import annotations

from collections import deque
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


def connected_background(rgb: np.ndarray, threshold: float = 18.0) -> np.ndarray:
    height, width, _ = rgb.shape
    border = np.concatenate(
        (rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]), axis=0
    ).astype(np.float32)
    background_color = np.median(border, axis=0)
    distance = np.linalg.norm(rgb.astype(np.float32) - background_color, axis=2)
    candidate = distance < threshold

    background = np.zeros((height, width), dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        if candidate[0, x]:
            queue.append((0, x))
        if candidate[height - 1, x]:
            queue.append((height - 1, x))
    for y in range(height):
        if candidate[y, 0]:
            queue.append((y, 0))
        if candidate[y, width - 1]:
            queue.append((y, width - 1))

    while queue:
        y, x = queue.popleft()
        if background[y, x] or not candidate[y, x]:
            continue
        background[y, x] = True
        if y:
            queue.append((y - 1, x))
        if y + 1 < height:
            queue.append((y + 1, x))
        if x:
            queue.append((y, x - 1))
        if x + 1 < width:
            queue.append((y, x + 1))
    return background


def extract_view(image: Image.Image, normalized_box: tuple[float, float, float, float]) -> Image.Image:
    left, top, right, bottom = normalized_box
    crop = image.crop(
        (
            round(image.width * left),
            round(image.height * top),
            round(image.width * right),
            round(image.height * bottom),
        )
    )
    rgb = np.asarray(crop)
    background = connected_background(rgb)
    alpha = np.where(background, 0, 255).astype(np.uint8)
    alpha_image = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.75))
    rgba = crop.convert("RGBA")
    rgba.putalpha(alpha_image)
    visible = alpha > 20
    ys, xs = np.where(visible)
    if len(xs) == 0:
        raise RuntimeError("No foreground pixels found")
    pad = 10
    return rgba.crop(
        (
            max(0, int(xs.min()) - pad),
            max(0, int(ys.min()) - pad),
            min(crop.width, int(xs.max()) + pad + 1),
            min(crop.height, int(ys.max()) + pad + 1),
        )
    )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_asset.py SOURCE OUTPUT")

    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    image = Image.open(source).convert("RGB")

    rgba = extract_view(image, (0.085, 0.008, 0.344, 0.993))
    output.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(output, optimize=True)
    side = extract_view(image, (0.355, 0.008, 0.680, 0.993))
    side_path = output.with_name("side.png")
    side.save(side_path, optimize=True)
    back = extract_view(image, (0.680, 0.008, 0.960, 0.993))
    back_path = output.with_name("back.png")
    back.save(back_path, optimize=True)

    icon = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    draw.ellipse((8, 8, 248, 248), fill=(255, 239, 249, 255), outline=(218, 174, 207, 255), width=5)
    head = rgba.crop((0, 0, rgba.width, min(rgba.height, round(rgba.width * 1.28))))
    head = ImageOps.contain(head, (222, 240), Image.Resampling.LANCZOS)
    icon.alpha_composite(head, ((256 - head.width) // 2, 15))
    icon_path = output.with_suffix(".ico")
    icon.save(icon_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(
        f"saved {output} {rgba.size}, {side_path} {side.size}, "
        f"{back_path} {back.size}, and {icon_path}"
    )


if __name__ == "__main__":
    main()
